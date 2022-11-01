const { PrivateMessage, Comment, snoowrap } = require("snoowrap")
const { saveTag, removeTag, db } = require("../index")

/**
 * 
 * @param {Array} args 
 * @param {PrivateMessage | Comment} mention 
 */
module.exports = async ( args, mention, reply, client ) => {
    if(!args[1]) return reply("This command requires arguments but none were passed, Stoopid mod \^\^")

    
    if(args[1] === "save") {
        if(!args[2]) return reply("You need to specify what to save the tag as")
        client.getComment(mention.parent_id).body.then(tag => {
            saveTag(args[2], tag)
            return reply(`Aight boss! Saved tag \`${args[2]}\``)
        })
    }

    if(args[1] === "delete") {
        if(!args[2]) return reply("You need to specify what tag to delete")
        removeTag(args[2])
        return reply(`Aight boss. Removed tag \`${args[2]}\``)
    }

    if(args[1] === "list") {
        const tags = db.prepare("SELECT id FROM tags").all()
        console.log(tags)
        if(tags.length === 0) return reply("There are no tags registered :(")
        return reply(`There are **${tags.length}** tag(s) registered!\n\n${tags.map(i => `\`${i.id}\``).join(", ")}`)
    }
}