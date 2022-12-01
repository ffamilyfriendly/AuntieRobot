/**
 * If you are reading this you are henceforth bound by license to listen and enjoy this song
 * https://www.youtube.com/watch?v=-gnDyhN5ilM
 * thanks // AuntieRob
 */

const snoowrap = require("snoowrap"),
    config = require("../config"),
    fs = require("fs"),
    rollcalls = JSON.parse(fs.readFileSync("./FlairAssign/rollcalls.json", "utf-8")),
    years = Object.keys(rollcalls).reverse()

const client = new snoowrap({
    userAgent: "AutieRobot",
    clientId: config.clientID,
    clientSecret: config.clientSecret,
    username: config.username,
    password: config.password
})

console.log(years.map(y => `${y}:\n - ${rollcalls[y].posts.length} rollcalls\n - ${rollcalls[y].required} answers required\n`).join("\n") + "\n")

/**
 * 
 * @param {String} url 
 * @returns 
 */
const postID = (url) => url.replace(/.*\/comments\/(\w+)\/.*/gm, (_s, group) => group)

const checkYear = (year) => {
    const users = new Map()

    /**
     * 
     * @param {String} text 
     * @returns 
     */
    const cleanText = (text) => text.toLowerCase().replace(/[^\w ]|\d/gm, "")

    return new Promise( async (resolve, reject) => {
        if(year != "2022") return reject( { text: "fecked" } )
        console.log(`📅 year ${year}`)
        const yearData = rollcalls[year]
        for(let index = 0; index < yearData.posts.length; index++) {
            const rollcall = yearData.posts[index]
            const id = postID(rollcall)

            const post = await client.getSubmission(id).expandReplies({ depth: 0 })
            console.log(`🔎 [${index+1}/${yearData.posts.length}]   Post ${post.title} (${id})  ${ index === 0 ? "(🚦FIRST POST🚦)" : "" }${ index + 1 === yearData.posts.length ? "(🏁LAST POST🏁)" : "" }`)
            for(const comment of post.comments) {
                const [ user, text ] = [ comment.author.name, cleanText(comment.body) ]

                const userData = users.get(user) || []

                if( [ "im in", "still in" ].some(el => text.includes(el)) ) {
                    // in
                    userData.push({ day: index, verdict: "in", response: comment.permalink  })
                } else if( [ "im out", "i lost" ].some(el => text.includes(el)) ) {
                    // out
                    userData.push({ day: index, verdict: "out", response: comment.permalink  })
                } else {
                    // uncertain
                    userData.push({ day: index, verdict: "uncertain", response: comment.permalink  })
                }
                users.set(user, userData)
            }
        }

        resolve(users)
    })
}

const checkFlairs = async () => {
    for(const year of years)  {
        const data = await checkYear(year).catch(e => console.error(e))
        console.log(data)
    }
}

checkFlairs()