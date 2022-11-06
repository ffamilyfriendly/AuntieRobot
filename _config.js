module.exports = {
    username: "AuntieRobot",
    password: "secret",
    clientID: "secret",
    clientSecret: "secret",
    subreddits: [ "nonutnovember", "auntierobot" ],

    // How often the bot will check for new mentions
    pollRate: 1000 * 20,
    // How often the bot will check new posts for triggers
    newPollRate: 1000 * 60,
    // Check how often to check bots responses score
    checkPostsPollRate: 1000 * 60 * 10,
    // If comment made by bot has below this score the response will be deleted
    removalLimit: -1,

    /**
     * Automatic triggers.
     * If a posts text contains any of the keywords the tag will be automatically called
     * 
     * format:
     * [
     *  [ { all: [], any: [], none: [] }, "tag" ]
     * ]
    */
    triggers: [
        [
            { all: [ "dream" ], any: [ "woke up", "sleep", "wet", "lucid" ], none: [] }, "dream"
        ],
        [
            { all: [ "dec" ], any: [ "continue", "make up", "failed" ], none: [] }, "excused"
        ],
        [
            { all: [  ], any: [ "prenut" ], none: [] }, "nutting"
        ]
    ],

    textFooter: "\n\n---\nThis action was performed *Auto-Magically™*. View the source code [HERE](https://github.com/ffamilyfriendly/AuntieRobot). Any questions regarding the bot are to be sent to u\/AuntieRob\n\n^This ^answer ^was ^made ^automatically. ^Downvote ^this ^comment ^if ^answer ^is ^irrelevant"
    
}