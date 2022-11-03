const snoowrap = require("snoowrap"),
    config = require("./config"),
    db = require("better-sqlite3")("reddit.db"),
    fs = require("fs")


const client = new snoowrap({
    userAgent: "AutieRobot",
    clientId: config.clientID,
    clientSecret: config.clientSecret,
    username: config.username,
    password: config.password
})

const dbCache = new Map()
const modCache = new Map()
const tags = new Map()

let rollcall = { date: 0, post: null }

const getRollCall = async () => {
    if(!rollcall.post || (rollcall.date + (1000 * 60 * 60) < Date.now())) {
        const post = (await client.getSubreddit("nonutnovember").search({ query: `flair:"🗳️ Official Roll-Call"`, sort: "new", time: "day" }))[0]
        rollcall = { date: Date.now(), post }
    }

    return rollcall.post
}

const saveTag = (name, value) => {
    tags.set(name, value)
    db.prepare("REPLACE INTO tags (id, text) VALUES(?,?)").run(name, value)
}

const getTag = (name) => {
    if(tags.has(name)) return tags.get(name)
    else {
        const res = db.prepare("SELECT text FROM tags WHERE id = ?").get(name)
        if(!res) return null
        tags.set(name, res.text)
        return res.text
    }
}

const removeTag = (name) => {
    if(tags.has(name)) tags.delete(name)
    db.prepare("DELETE FROM tags WHERE id = ?").run(name)
}

module.exports = { db, saveTag, getTag, removeTag }

const commands = new Map(fs.readdirSync('./commands').filter((f) => f.endsWith('.js')).map((f) => [f.split('.js')[0], require(`./commands/${f}`)]));

db.prepare("CREATE TABLE IF NOT EXISTS handled (id TEXT PRIMARY KEY, reply TEXT NOT NULL)").run()
db.prepare("CREATE TABLE IF NOT EXISTS tags (id TEXT PRIMARY KEY, text TEXT NOT NULL)").run()

const hasReplied = (commentId) => {
    if(dbCache.has(commentId)) return dbCache.get(commentId)
    else {
        const res = db.prepare("SELECT * FROM handled WHERE id = ?").get(commentId)
        if(res) {
            dbCache.set(commentId, res)
            return res
        } else return false
    }
}

const setReplied = (commentId, replyId) => {
    dbCache.set(commentId, replyId)
    db.prepare("INSERT INTO handled (id, reply) VALUES(?,?)").run(commentId, replyId)
}

const getMods = (subreddit) => {
    return new Promise((resolve, reject) => {
        client.getSubreddit(subreddit).getModerators().then((mods) => {
            let modArr = []
            for(const mod of mods)
                modArr.push(mod.name)
            resolve(modArr)
        })
    })
}

const text = (t) => `${t}${config.textFooter}`

const getMentions = async () => {
    const mentions = await client.getInbox({ filter: "mentions" })

    for(const mention of mentions) {

        // If subreddit bot is tagged in aint in the subreddits array we wont respond
        if(!config.subreddits.includes(mention.subreddit.display_name.toLowerCase())) return

        // Ensure the moderators of this subreddit has been cached
        if(!modCache.has(mention.subreddit.display_name)) modCache.set(mention.subreddit.display_name, await getMods(mention.subreddit.display_name))
        
        // Check if user is mod in this subreddit
        if(!modCache.get(mention.subreddit.display_name).includes(mention.author.name)) return

        // Ensure that the user tag is the first part of the comment
        if(!mention.body.toLowerCase().startsWith("u/auntierobot")) return

        // Check if bot has already handles this u/mention
        if(hasReplied(mention.id)) return

        const args = mention.body.split(" ").slice(1)

        const reply = (content) => {
            mention.reply(text(content)).then(r => {
                setReplied(mention.id, r.id)
            })
        }

        const replaceInlineValues = async (str) => {

            const d = new Date()

            const values = {
                rollcall: await getRollCall(),
                date: {
                    day: d.getDate().toString().padStart(2, "0"),
                    month: d.getMonth().toString().padStart(2, "0"),
                    year: d.getFullYear()
                },
                mention: mention
            }

            str = str.replaceAll(/{.*?}/gi, (param) => {
                param = param.replace(/{|}/gi, "")

                let params = param.split(".")
                
                let obj = null
                for(const i of params) {

                    if(!obj && !values[i]) {
                        obj = param
                        break;
                    }

                    if(!obj && values[i]) obj = values[i]
                    else {
                        if(obj[i]) obj = obj[i]
                    }
                }

                return obj
            })

            return str
        }

        console.log(`Handling mention from ${mention.author.name} in ${mention.subreddit.display_name}: ${args.join(" ")}`)

        if(commands.has(args[0])) {
            commands.get(args[0])( args, mention, reply, client )
        } else {
            let tags = []

            for(const tagname of args)
                tags.push(await replaceInlineValues(getTag(tagname)))

            if(tags.length !== 0) {
                client.getComment(mention.parent_id)
                    .reply(text(tags.join("\n\n")))
                    .then(r => {
                        setReplied(mention.id, r.id)
                        try {
                            r.distinguish({ status: true, sticky: true })
                        } catch(err) {
                            console.log(`failed to distiguish reply with id "${r.id}". `, err)
                        }
                    })
            }
        }
    }
}

const getNewPosts = async () => {
    const posts = await client.getSubreddit("auntierobot").getNew({ limit: 10,  })

    for(const post of posts) {
        // Ensure the moderators of this subreddit has been cached
        //if(!modCache.has(post.subreddit.display_name)) modCache.set(post.subreddit.display_name, await getMods(post.subreddit.display_name))
        
        // Check if user is mod in this subreddit. If mod, assume mod is not asking a common question, ignore mods post
        //if(modCache.get(post.subreddit.display_name).includes(post.author.name)) return

        // Check if bot has already handles this u/mention
        if(hasReplied(post.id)) return

        // if post has no text, ignore. TODO: add check for that fucking coupon image
        //if(!post.selftext) return

        const keywords = [ ...post.selftext.toLowerCase().split(" "), ...post.title.toLowerCase().split(" ") ]

        let tags = [ ]

        const replaceInlineValues = async (str) => {

            const d = new Date()

            const values = {
                rollcall: await getRollCall(),
                date: {
                    day: d.getDate().toString().padStart(2, "0"),
                    month: d.getMonth().toString().padStart(2, "0"),
                    year: d.getFullYear()
                },
                mention: post
            }

            str = str.replaceAll(/{.*?}/gi, (param) => {
                param = param.replace(/{|}/gi, "")

                let params = param.split(".")
                
                let obj = null
                for(const i of params) {

                    if(!obj && !values[i]) {
                        obj = param
                        break;
                    }

                    if(!obj && values[i]) obj = values[i]
                    else {
                        if(obj[i]) obj = obj[i]
                    }
                }

                return obj
            })

            return str
        }

        for(const trigger of config.triggers) {
            for(const word of keywords) {
                if(trigger[0].includes(word) && !tags.includes(trigger[1])) tags.push(await replaceInlineValues(getTag(trigger[1])))
            }
        }

        if(tags.length === 0) {
            setReplied(post.id, "postOK")
        } else {
            console.log(`Post with id ${post.id} `)
            post.reply(text(tags.join("\n\n"))).then(r => {
                setReplied(post.id, r.id)
            })
        }
    }
}

getMentions()
getNewPosts()

setInterval(getMentions, config.pollRate)
setInterval(getNewPosts, config.newPollRate)