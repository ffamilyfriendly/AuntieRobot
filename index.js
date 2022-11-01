const snoowrap = require("snoowrap"),
    config = require("./config"),
    db = require("better-sqlite3")("reddit.db")


const client = new snoowrap({
    userAgent: "AutieRobot",
    clientId: config.clientID,
    clientSecret: config.clientSecret,
    username: config.username,
    password: config.password
})

let dbCache = new Map()
let modCache = new Map()

db.prepare("CREATE TABLE IF NOT EXISTS handled (id TEXT PRIMARY KEY, reply TEXT NOT NULL)").run()
db.prepare("CREATE NEW TABLE tags (id TEXT PRIMARY KEY, text TEXT NOT NULL)")

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
    console.log("Beep boop, fetching mentions...")
    const mentions = await client.getInbox({ filter: "mentions" })

    for(const mention of mentions) {
        // If subreddit bot is tagged in aint in the subreddits array we wont respond
        if(!config.subreddits.includes(mention.subreddit.display_name)) return

        // Ensure the moderators of this subreddit has been cached
        if(!modCache.has(mention.subreddit.display_name)) modCache.set(mention.subreddit.display_name, await getMods(mention.subreddit.display_name))
        
        // Check if user is mod in this subreddit
        if(!modCache.get(mention.subreddit.display_name).includes(mention.author.name)) return

        console.log(mention.body)

        // Check if bot has already handles this u/mention
        if(hasReplied(mention.id)) return

        const args = mention.body.split(" ").slice(1)

        setReplied(mention.id, "TEST")
    }
}

getMentions()

setInterval(getMentions, config.pollRate)