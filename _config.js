module.exports = {
    username: "AuntieRobot",
    password: "secret",
    clientID: "y",
    clientSecret: "y",
    subreddits: [ "subreddit" ],

    // How often the bot will check for new mentions
    pollRate: 1000 * 20,
    // How often the bot will check new posts for triggers
    newPollRate: 1000 * 60,

    /**
     * Automatic triggers.
     * If a posts text contains any of the keywords the tag will be automatically called
     * 
     * format:
     * [
     *  [ [ KEYWORDS ], "tag" ]
     * ]
    */
    triggers: [
        [
            [ "dream", "woke up", "lucid", "dreams", "sleep" ], "dream"
        ],
        [
            [ "did i fail", "did i" ], "didi"
        ],
        [
            [ "coupon", "these work" ], "coupon"
        ],
        [
            ["can i", "have sex", "edge", "watch porn"], "cani"
        ],
        [
            ["precum"], "nutting"
        ]
    ],
    
    textFooter: "\n\n---\nThis action was performed *Auto-Magically™*. View the source code [HERE](https://github.com/ffamilyfriendly/AuntieRobot). Any questions regarding the bot are to be sent to u\/AuntieRob"
}