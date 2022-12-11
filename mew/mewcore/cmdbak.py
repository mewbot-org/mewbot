bak = [
    {
        "id": "888886898158862376",
        "application_id": "519850436899897346",
        "version": "888886898158862377",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "nitro",
        "description": "Claim rewards for boosting the Mewbot Official Server.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "claim",
                "description": "Claim rewards for boosting the Mewbot Official Server.",
            }
        ],
    },
    {
        "id": "888886906849484832",
        "application_id": "519850436899897346",
        "version": "923390802657415168",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "breed",
        "description": "Breed two pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "pokes",
                "description": "The pokemon numbers of the two pokemon to breed, separated by a space.",
                "required": True,
            }
        ],
    },
    {
        "id": "888886916211150859",
        "application_id": "519850436899897346",
        "version": "888886916211150860",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "breedswith",
        "description": "Filter your pokemon to show only ones that can breed with the provided pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 4,
                "name": "poke",
                "description": "The pokemon that will be used to check compatibility.",
                "required": True,
            },
            {
                "type": 3,
                "name": "filter_args",
                "description": "Extra arguments to filter with. See /filter for more information.",
            },
        ],
    },
    {
        "id": "888886925493145630",
        "application_id": "519850436899897346",
        "version": "888886925493145631",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "daycare",
        "description": "View your unhatched eggs.",
        "dm_permission": True,
    },
    {
        "id": "888886934448009246",
        "application_id": "519850436899897346",
        "version": "931616774896615434",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "open",
        "description": "Open a radiant chest.",
        "dm_permission": True,
        "options": [
            {"type": 1, "name": "common", "description": "Open a common chest."},
            {"type": 1, "name": "rare", "description": "Open a rare chest."},
            {"type": 1, "name": "mythic", "description": "Open a mythic chest."},
            {"type": 1, "name": "legend", "description": "Open a legend chest."},
        ],
    },
    {
        "id": "888886982514720778",
        "application_id": "519850436899897346",
        "version": "903785699424215041",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "radiant",
        "description": "Spend your radiant gems.",
        "dm_permission": True,
        "options": [
            {
                "type": 4,
                "name": "pack",
                "description": "The pack number to buy. Do not pass this arg to view the packs.",
                "choices": [
                    {"name": "1. Shiny Multiplier x1", "value": 1},
                    {"name": "2. Battle Multiplier x1", "value": 2},
                    {"name": "3. IV Multiplier x1", "value": 3},
                    {"name": "4. Breeding Multiplier x1", "value": 4},
                    {"name": "5. Legend Chest", "value": 5},
                    {"name": "6. Radiant Pokemon (non-legend)", "value": 6},
                    {"name": "7. Radiant Pokemon (rare)", "value": 7},
                    {"name": "8. Radiant Pokemon (legend)", "value": 8},
                ],
            }
        ],
    },
    {
        "id": "888886991712833546",
        "application_id": "519850436899897346",
        "version": "990413034952486963",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "duel",
        "description": "Engage in a pokemon duel.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "single",
                "description": "Duel another player with your selected pokemon.",
                "options": [
                    {
                        "type": 6,
                        "name": "user",
                        "description": "The user to duel.",
                        "required": True,
                    }
                ],
            },
            {
                "type": 1,
                "name": "party",
                "description": "Duel another player with your configured party of pokemon.",
                "options": [
                    {
                        "type": 6,
                        "name": "user",
                        "description": "The user to duel.",
                        "required": True,
                    }
                ],
            },
            {
                "type": 1,
                "name": "inverse",
                "description": "Duel another player with your configured party of pokemon in the inverse battle format.",
                "options": [
                    {
                        "type": 6,
                        "name": "user",
                        "description": "The user to duel.",
                        "required": True,
                    }
                ],
            },
            {
                "type": 1,
                "name": "npc",
                "description": "Duel an NPC AI with your selected pokemon.",
            },
        ],
    },
    {
        "id": "888887000680267846",
        "application_id": "519850436899897346",
        "version": "975497032506703902",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "add",
        "description": "Add evs to your selected pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "evs",
                "description": "Add evs to your selected pokemon.",
                "options": [
                    {
                        "type": 4,
                        "name": "amount",
                        "description": "The amount of ev points to add.",
                        "required": True,
                    },
                    {
                        "type": 3,
                        "name": "stat",
                        "description": "The stat to add ev points to.",
                        "required": True,
                        "choices": [
                            {"name": "HP", "value": "hp"},
                            {"name": "Attack", "value": "attack"},
                            {"name": "Defense", "value": "defense"},
                            {"name": "Special Attack", "value": "special attack"},
                            {"name": "Special Defense", "value": "special defense"},
                            {"name": "Speed", "value": "speed"},
                        ],
                    },
                ],
            }
        ],
    },
    {
        "id": "888887010058711050",
        "application_id": "519850436899897346",
        "version": "931616689471242320",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "spread",
        "description": "Spread honey in your server to attract rare pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "honey",
                "description": "Spread honey in your server to attract rare pokemon.",
            }
        ],
    },
    {
        "id": "888887019202281472",
        "application_id": "519850436899897346",
        "version": "888887019202281473",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "server",
        "description": "View stats abour your server.",
        "dm_permission": True,
    },
    {
        "id": "888887066992185454",
        "application_id": "519850436899897346",
        "version": "938144901273640970",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "change",
        "description": "Change the nature of your selected pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "nature",
                "description": "Change the nature of your selected pokemon.",
                "options": [
                    {
                        "type": 3,
                        "name": "nature",
                        "description": "The nature to make your selected pokemon.",
                        "required": True,
                        "choices": [
                            {"name": "Hardy (+atk/-atk)", "value": "hardy"},
                            {"name": "Bold (+def/-atk)", "value": "bold"},
                            {"name": "Modest (+spatk/-atk)", "value": "modest"},
                            {"name": "Calm (+spdef/-atk)", "value": "calm"},
                            {"name": "Timid (+speed/-atk)", "value": "timid"},
                            {"name": "Lonely (+atk/-def)", "value": "lonely"},
                            {"name": "Docile (+def/-def)", "value": "docile"},
                            {"name": "Mild (+spatk/-def)", "value": "mild"},
                            {"name": "Gentle (+spdef/-def)", "value": "gentle"},
                            {"name": "Hasty (+speed/-def)", "value": "hasty"},
                            {"name": "Adamant (+atk/-spatk)", "value": "adamant"},
                            {"name": "Impish (+def/-spatk)", "value": "impish"},
                            {"name": "Bashful (+spatk/-spatk)", "value": "bashful"},
                            {"name": "Careful (+spdef/-spatk)", "value": "careful"},
                            {"name": "Jolly (+speed/-spatk)", "value": "jolly"},
                            {"name": "Naughty (+atk/-spdef)", "value": "naughty"},
                            {"name": "Lax (+def/-spdef)", "value": "lax"},
                            {"name": "Rash (+spatk/-spdef)", "value": "rash"},
                            {"name": "Quirky (+spdef/-spdef)", "value": "quirky"},
                            {"name": "Naive (+speed/-spdef)", "value": "naive"},
                            {"name": "Brave (+atk/-speed)", "value": "brave"},
                            {"name": "Relaxed (+def/-speed)", "value": "relaxed"},
                            {"name": "Quiet (+spatk/-speed)", "value": "quiet"},
                            {"name": "Sassy (+spdef/-speed)", "value": "sassy"},
                            {"name": "Serious (+speed/-speed)", "value": "serious"},
                        ],
                    }
                ],
            }
        ],
    },
    {
        "id": "888887076056092683",
        "application_id": "519850436899897346",
        "version": "888887076056092684",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "bag",
        "description": "View the contents of your bag.",
        "dm_permission": True,
    },
    {
        "id": "888887085107413033",
        "application_id": "519850436899897346",
        "version": "888887085107413034",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "unequip",
        "description": "Unequip the held item from your selected pokemon.",
        "dm_permission": True,
    },
    {
        "id": "888887094104162304",
        "application_id": "519850436899897346",
        "version": "888887094104162305",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "equip",
        "description": "Equip a held item on your selected pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "item",
                "description": "The item to equip.",
                "required": True,
            }
        ],
    },
    {
        "id": "888887103079997490",
        "application_id": "519850436899897346",
        "version": "888887103079997491",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "apply",
        "description": "Apply an item to your selected pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "item",
                "description": "The item to apply.",
                "required": True,
            }
        ],
    },
    {
        "id": "888887151146717205",
        "application_id": "519850436899897346",
        "version": "888887151146717206",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "visible",
        "description": "Toggle allowing others to view your /bal.",
        "dm_permission": True,
    },
    {
        "id": "888887160483241984",
        "application_id": "519850436899897346",
        "version": "888887160483241985",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "updates",
        "description": "View recent updates to the bot.",
        "dm_permission": True,
    },
    {
        "id": "888887169245130753",
        "application_id": "519850436899897346",
        "version": "974442178002681907",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "silence",
        "description": "Toggle silencing level up messages for your pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "user",
                "description": "Toggle silencing level up messages for your pokemon.",
            },
            {
                "type": 1,
                "name": "server",
                "description": "Toggle silencing level up messages for all pokemon in this server.",
            },
        ],
    },
    {
        "id": "888887178774593536",
        "application_id": "519850436899897346",
        "version": "888887178774593537",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "status",
        "description": "View some statistics about mewbot.",
        "dm_permission": True,
    },
    {
        "id": "888887187762978856",
        "application_id": "519850436899897346",
        "version": "888887187762978857",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "claim",
        "description": "Claim rewards in exchange for 5 upvote points.",
        "dm_permission": True,
    },
    {
        "id": "888887235833905193",
        "application_id": "519850436899897346",
        "version": "965415000799838258",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "ping",
        "description": "Pong!",
        "dm_permission": True,
    },
    {
        "id": "888887248039317514",
        "application_id": "519850436899897346",
        "version": "888887248039317515",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "vote",
        "description": "Upvote the bot and get upvote points.",
        "dm_permission": True,
    },
    {
        "id": "888887256612495471",
        "application_id": "519850436899897346",
        "version": "888887256612495472",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "predeem",
        "description": "Claim redeems for being a patreon.",
        "dm_permission": True,
    },
    {
        "id": "888887266183905332",
        "application_id": "519850436899897346",
        "version": "888887266183905333",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "nick",
        "description": "Change your pokemon's nickname.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "nick",
                "description": "The nickname to set it as. Leave blank to clear.",
            }
        ],
    },
    {
        "id": "888887275235209246",
        "application_id": "519850436899897346",
        "version": "888887275235209247",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "stats",
        "description": "Show some stats about yourself.",
        "dm_permission": True,
    },
    {
        "id": "888887320458194964",
        "application_id": "519850436899897346",
        "version": "888887320458194965",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "trainer",
        "description": "Show your trainer card, or the trainer card of another member.",
        "dm_permission": True,
        "options": [
            {
                "type": 6,
                "name": "user",
                "description": "The user who's card will be shown. Leave blank to show your card.",
            }
        ],
    },
    {
        "id": "888887329496895518",
        "application_id": "519850436899897346",
        "version": "888887329496895519",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "trainernick",
        "description": "Change your trainer nickname, which is shown on pokemon you catch.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "nick",
                "description": "The nickname to set it as.",
                "required": True,
            }
        ],
    },
    {
        "id": "888887338493685812",
        "application_id": "519850436899897346",
        "version": "888887338493685813",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "invite",
        "description": "Invite Mewbot to your server.",
        "dm_permission": True,
    },
    {
        "id": "888887347519828058",
        "application_id": "519850436899897346",
        "version": "888887347519828059",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "bal",
        "description": "Show your balance, or the balance of another member.",
        "dm_permission": True,
        "options": [
            {
                "type": 6,
                "name": "user",
                "description": "The user who's balance will be shown. Leave blank to show your balance.",
            }
        ],
    },
    {
        "id": "888887356545957928",
        "application_id": "519850436899897346",
        "version": "888887356545957929",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "fav",
        "description": "View your pokedex.",
        "dm_permission": True,
        "options": [
            {"type": 1, "name": "list", "description": "List your favorite pokemon."},
            {
                "type": 1,
                "name": "add",
                "description": "Add a pokemon to your favorites.",
                "options": [
                    {
                        "type": 4,
                        "name": "poke",
                        "description": "The pokemon number to add. If not provided, your selected pokemon is used instead.",
                    }
                ],
            },
            {
                "type": 1,
                "name": "remove",
                "description": "Remove a pokemon from your favorites.",
                "options": [
                    {
                        "type": 4,
                        "name": "poke",
                        "description": "The pokemon number to remove. If not provided, your selected pokemon is used instead.",
                    }
                ],
            },
        ],
    },
    {
        "id": "888887405057306654",
        "application_id": "519850436899897346",
        "version": "904170459216621618",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "f",
        "description": "Filter your pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "m",
                "description": "Filter the market.",
                "options": [
                    {
                        "type": 3,
                        "name": "args",
                        "description": "Arguments to filter with. For more information about this, see /tutorial.",
                    }
                ],
            },
            {
                "type": 1,
                "name": "p",
                "description": "Filter your pokemon.",
                "options": [
                    {
                        "type": 3,
                        "name": "args",
                        "description": "Arguments to filter with. For more information about this, see /tutorial.",
                    }
                ],
            },
        ],
    },
    {
        "id": "888887414062460968",
        "application_id": "519850436899897346",
        "version": "888887414062460969",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "fish",
        "description": "Fish for some pokemon.",
        "dm_permission": True,
    },
    {
        "id": "888887423147343964",
        "application_id": "519850436899897346",
        "version": "888887423147343965",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "lunarize",
        "description": "Lunarizes the selected Necrozma into Necrozma-dawn form.",
        "dm_permission": True,
        "options": [
            {
                "type": 4,
                "name": "lunala",
                "description": "The lunala to fuse with.",
                "required": True,
            }
        ],
    },
    {
        "id": "888887432240566312",
        "application_id": "519850436899897346",
        "version": "888887432240566313",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "solarize",
        "description": "Solarizes the selected Necrozma into Necrozma-dusk form.",
        "dm_permission": True,
        "options": [
            {
                "type": 4,
                "name": "solgaleo",
                "description": "The solgaleo to fuse with.",
                "required": True,
            }
        ],
    },
    {
        "id": "888887440989904927",
        "application_id": "519850436899897346",
        "version": "888887440989904928",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "fuse",
        "description": "Fuses the selected Kyurem or Calyrex to change its form.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "form",
                "description": "The form to make this poke.",
                "required": True,
            },
            {
                "type": 4,
                "name": "poke",
                "description": "The poke to fuse with.",
                "required": True,
            },
        ],
    },
    {
        "id": "888887489593507840",
        "application_id": "519850436899897346",
        "version": "888887489593507841",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "deform",
        "description": "Deforms your selected pokemon.",
        "dm_permission": True,
    },
    {
        "id": "888887498653192292",
        "application_id": "519850436899897346",
        "version": "888887498653192293",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "form",
        "description": "Forms your selected pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "form",
                "description": "The form to form into.",
                "required": True,
            }
        ],
    },
    {
        "id": "888887507830321152",
        "application_id": "519850436899897346",
        "version": "888887507830321153",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "mega",
        "description": "Mega evolve your selected pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "evolve",
                "description": "Mega evolve your selected pokemon.",
            },
            {
                "type": 1,
                "name": "devolve",
                "description": "Devolve your mega selected pokemon.",
            },
            {
                "type": 1,
                "name": "x",
                "description": "Mega-x evolve your selected pokemon.",
            },
            {
                "type": 1,
                "name": "y",
                "description": "Mega-y evolve your selected pokemon.",
            },
        ],
    },
    {
        "id": "888887516843892746",
        "application_id": "519850436899897346",
        "version": "888887516843892747",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "drop",
        "description": "Drop your selected pokemon's equipped item.",
        "dm_permission": True,
    },
    {
        "id": "888887525521911849",
        "application_id": "519850436899897346",
        "version": "888887525521911850",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "transfer",
        "description": "Transfer your selected pokemon's equipped item to another pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 4,
                "name": "poke",
                "description": "The pokemon number to transfer the item to",
                "required": True,
            }
        ],
    },
    {
        "id": "888887574196781066",
        "application_id": "519850436899897346",
        "version": "903788776600522792",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "buy",
        "description": "Buy items.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "item",
                "description": "Buy an item.",
                "options": [
                    {
                        "type": 3,
                        "name": "item",
                        "description": "The item to buy.",
                        "required": True,
                    }
                ],
            },
            {
                "type": 1,
                "name": "daycare",
                "description": "Buy a daycare space.",
                "options": [
                    {
                        "type": 4,
                        "name": "amount",
                        "description": "The number of spaces to buy. Defaults to 1.",
                    }
                ],
            },
            {
                "type": 1,
                "name": "coins",
                "description": "Buy coins.",
                "options": [
                    {
                        "type": 4,
                        "name": "amount",
                        "description": "The number of coins to buy.",
                        "required": True,
                    }
                ],
            },
            {
                "type": 1,
                "name": "vitamins",
                "description": "Buy vitamins to increase your selected pokemon's EVs.",
                "options": [
                    {
                        "type": 3,
                        "name": "vitamin",
                        "description": "The vitamin to buy.",
                        "required": True,
                        "choices": [
                            {"name": "HP Up (hp)", "value": "hp-up"},
                            {"name": "Protein (atk)", "value": "protein"},
                            {"name": "Iron (def)", "value": "iron"},
                            {"name": "Calcium (spatk)", "value": "calcium"},
                            {"name": "Zinc (spdef)", "value": "zinc"},
                            {"name": "Carbos (speed)", "value": "carbos"},
                        ],
                    },
                    {
                        "type": 4,
                        "name": "amount",
                        "description": "The number of vitamins to buy.",
                        "required": True,
                    },
                ],
            },
            {
                "type": 1,
                "name": "candy",
                "description": "Buy rare candy to level up your selected pokemon.",
                "options": [
                    {
                        "type": 4,
                        "name": "amount",
                        "description": "The number of rare candies to buy. Defaults to 1.",
                    }
                ],
            },
            {
                "type": 1,
                "name": "chest",
                "description": "Buy a radiant chest.",
                "options": [
                    {
                        "type": 3,
                        "name": "rarity",
                        "description": "The chest rarity to buy.",
                        "required": True,
                        "choices": [
                            {"name": "Rare", "value": "rare"},
                            {"name": "Mythic", "value": "mythic"},
                            {"name": "Legend", "value": "legend"},
                        ],
                    },
                    {
                        "type": 3,
                        "name": "credits_or_redeems",
                        "description": "Whether you want to spend credits or redeems.",
                        "required": True,
                        "choices": [
                            {"name": "Credits", "value": "credits"},
                            {"name": "Redeems", "value": "redeems"},
                        ],
                    },
                ],
            },
            {
                "type": 1,
                "name": "redeems",
                "description": "Buy redeems.",
                "options": [
                    {
                        "type": 4,
                        "name": "amount",
                        "description": "The amount to buy. Leave blank to view how many you can buy this week.",
                    }
                ],
            },
        ],
    },
    {
        "id": "888887583470395432",
        "application_id": "519850436899897346",
        "version": "888887583470395433",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "cash",
        "description": "Convert your coins to credits.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "out",
                "description": "Convert your coins to credits.",
                "options": [
                    {
                        "type": 4,
                        "name": "amount",
                        "description": "The amount of coins to convert.",
                        "required": True,
                    }
                ],
            }
        ],
    },
    {
        "id": "888887592207155302",
        "application_id": "519850436899897346",
        "version": "888887592207155303",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "m",
        "description": "Interact with the market.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "add",
                "description": "Add a pokemon to the market.",
                "options": [
                    {
                        "type": 4,
                        "name": "poke",
                        "description": "The pokemon to add to the market.",
                        "required": True,
                    },
                    {
                        "type": 4,
                        "name": "price",
                        "description": "The price to list the pokemon for.",
                        "required": True,
                    },
                ],
            },
            {
                "type": 1,
                "name": "buy",
                "description": "Buy a pokemon from the market.",
                "options": [
                    {
                        "type": 4,
                        "name": "listing_id",
                        "description": "The ID of the listing you want to buy.",
                        "required": True,
                    }
                ],
            },
            {
                "type": 1,
                "name": "remove",
                "description": "Remove your pokemon from the market",
                "options": [
                    {
                        "type": 4,
                        "name": "listing_id",
                        "description": "The ID of the listing you want to remove.",
                        "required": True,
                    }
                ],
            },
            {
                "type": 1,
                "name": "i",
                "description": "View information about a pokemon on the market.",
                "options": [
                    {
                        "type": 4,
                        "name": "listing_id",
                        "description": "The ID of the listing you want to view.",
                        "required": True,
                    }
                ],
            },
        ],
    },
    {
        "id": "888887601778536538",
        "application_id": "519850436899897346",
        "version": "888887601778536539",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "donate",
        "description": "Make a donation to the bot and get some redeems.",
        "dm_permission": True,
    },
    {
        "id": "888887610393649183",
        "application_id": "519850436899897346",
        "version": "888887610393649184",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "mission",
        "description": "View today's missions.",
        "dm_permission": True,
        "options": [
            {"type": 1, "name": "list", "description": "View today's missions."},
            {
                "type": 1,
                "name": "claim",
                "description": "Claim rewards for completing today's missions.",
            },
        ],
    },
    {
        "id": "888887658598785034",
        "application_id": "519850436899897346",
        "version": "902040102048501780",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "learn",
        "description": "Teach your selected pokemon a move.",
        "dm_permission": True,
        "options": [
            {
                "type": 4,
                "name": "slot",
                "description": "The move slot to learn this move in.",
                "required": True,
                "choices": [
                    {"name": "Slot 1", "value": 1},
                    {"name": "Slot 2", "value": 2},
                    {"name": "Slot 3", "value": 3},
                    {"name": "Slot 4", "value": 4},
                ],
            },
            {
                "type": 3,
                "name": "move",
                "description": "The move to learn.",
                "required": True,
            },
        ],
    },
    {
        "id": "888887667666853908",
        "application_id": "519850436899897346",
        "version": "888887667666853909",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "moves",
        "description": "View the moves of your selected pokemon.",
        "dm_permission": True,
    },
    {
        "id": "888887676487487499",
        "application_id": "519850436899897346",
        "version": "888887676487487500",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "moveset",
        "description": "View the learnable moves of your selected pokemon.",
        "dm_permission": True,
    },
    {
        "id": "888887685534609499",
        "application_id": "519850436899897346",
        "version": "888887685534609500",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "order",
        "description": "Change the default order of your pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "ivs",
                "description": "Change the default order of your pokemon to sort by IVs.",
            },
            {
                "type": 1,
                "name": "default",
                "description": "Change the default order of your pokemon to the default.",
            },
            {
                "type": 1,
                "name": "evs",
                "description": "Change the default order of your pokemon to sort by EVs.",
            },
            {
                "type": 1,
                "name": "name",
                "description": "Change the default order of your pokemon to sort by name.",
            },
            {
                "type": 1,
                "name": "level",
                "description": "Change the default order of your pokemon to sort by level.",
            },
        ],
    },
    {
        "id": "888887694887907398",
        "application_id": "519850436899897346",
        "version": "928455470635687957",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "party",
        "description": "Manage your party.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "view",
                "description": "View the pokemon currently in your party.",
            },
            {
                "type": 1,
                "name": "add",
                "description": "Add a pokemon to your party.",
                "options": [
                    {
                        "type": 4,
                        "name": "slot",
                        "description": "The party slot to add the pokemon in.",
                        "required": True,
                        "choices": [
                            {"name": "Slot 1", "value": 1},
                            {"name": "Slot 2", "value": 2},
                            {"name": "Slot 3", "value": 3},
                            {"name": "Slot 4", "value": 4},
                            {"name": "Slot 5", "value": 5},
                            {"name": "Slot 6", "value": 6},
                        ],
                    },
                    {
                        "type": 4,
                        "name": "poke",
                        "description": "The pokemon you want to add. Leave blank to add your selected pokemon.",
                    },
                ],
            },
            {
                "type": 1,
                "name": "remove",
                "description": "Remove a pokemon from your party.",
                "options": [
                    {
                        "type": 4,
                        "name": "slot",
                        "description": "The party slot to remove the pokemon from.",
                        "required": True,
                    }
                ],
            },
            {
                "type": 1,
                "name": "register",
                "description": "Register your current party so it can be loaded again later.",
                "options": [
                    {
                        "type": 3,
                        "name": "name",
                        "description": "The name to register your party under.",
                        "required": True,
                    }
                ],
            },
            {
                "type": 1,
                "name": "deregister",
                "description": "Deregister a party, removing it from your saved parties.",
                "options": [
                    {
                        "type": 3,
                        "name": "name",
                        "description": "The name of the party to deregister.",
                        "required": True,
                    }
                ],
            },
            {
                "type": 1,
                "name": "load",
                "description": "Load a party you previously registered.",
                "options": [
                    {
                        "type": 3,
                        "name": "name",
                        "description": "The name of the party to load.",
                        "required": True,
                    }
                ],
            },
            {"type": 1, "name": "list", "description": "List your registered parties."},
        ],
    },
    {
        "id": "888887742832988191",
        "application_id": "519850436899897346",
        "version": "888887742832988192",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "pokedex",
        "description": "View your pokedex.",
        "dm_permission": True,
        "options": [
            {"type": 1, "name": "national", "description": "View your pokedex."},
            {"type": 1, "name": "unowned", "description": "View your unowned pokemon."},
        ],
    },
    {
        "id": "888887752127574036",
        "application_id": "519850436899897346",
        "version": "888887752127574037",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "select",
        "description": "Select a pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "poke",
                "description": 'The pokemon number to select, or "new".',
                "required": True,
            }
        ],
    },
    {
        "id": "888887760784605185",
        "application_id": "519850436899897346",
        "version": "888887760784605186",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "release",
        "description": "Release a pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "poke",
                "description": 'The pokemon number to release, or "new".',
                "required": True,
            }
        ],
    },
    {
        "id": "888887779457642546",
        "application_id": "519850436899897346",
        "version": "888887779457642547",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "p",
        "description": "List your owned pokemon.",
        "dm_permission": True,
    },
    {
        "id": "888887827771826196",
        "application_id": "519850436899897346",
        "version": "888887827771826197",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "tags",
        "description": "Add tags to your pokemon for easy filtering.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "list",
                "description": "View the tags on a pokemon.",
                "options": [
                    {
                        "type": 3,
                        "name": "poke",
                        "description": 'The pokemon number, or "new".',
                        "required": True,
                    }
                ],
            },
            {
                "type": 1,
                "name": "add",
                "description": "Add a tag to one or more pokemon.",
                "options": [
                    {
                        "type": 3,
                        "name": "tag",
                        "description": "The tag to add.",
                        "required": True,
                    },
                    {
                        "type": 3,
                        "name": "pokes",
                        "description": 'The pokemon number(s), or "new".',
                        "required": True,
                    },
                ],
            },
            {
                "type": 1,
                "name": "remove",
                "description": "Remove a tag from one or more pokemon.",
                "options": [
                    {
                        "type": 3,
                        "name": "tag",
                        "description": "The tag to remove.",
                        "required": True,
                    },
                    {
                        "type": 3,
                        "name": "pokes",
                        "description": 'The pokemon number(s), or "new".',
                        "required": True,
                    },
                ],
            },
        ],
    },
    {
        "id": "888887837037039646",
        "application_id": "519850436899897346",
        "version": "888887837037039647",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "i",
        "description": "View information on a pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "poke",
                "description": 'The pokemon number, or "new". If not provided, your selected pokemon is used instead.',
            }
        ],
    },
    {
        "id": "888887846205804564",
        "application_id": "519850436899897346",
        "version": "888887846205804565",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "qi",
        "description": "View information on a pokemon in a more compact format.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "poke",
                "description": 'The pokemon number, or "new". If not provided, your selected pokemon is used instead.',
            }
        ],
    },
    {
        "id": "888887855445868595",
        "application_id": "519850436899897346",
        "version": "888887855445868596",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "packs",
        "description": "View the different redeemable packs.",
        "dm_permission": True,
    },
    {
        "id": "888887864497172510",
        "application_id": "519850436899897346",
        "version": "888887864497172511",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "redeem",
        "description": "Spend your redeems.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "item",
                "description": "What you want to buy with your redeems. Leave blank to see what you can buy.",
            }
        ],
    },
    {
        "id": "888887912102494239",
        "application_id": "519850436899897346",
        "version": "928915358075715594",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "redeemmultiple",
        "description": "Redeem multiple of the same item at once.",
        "dm_permission": True,
        "options": [
            {
                "type": 4,
                "name": "amount",
                "description": "The number of the item to redeem.",
                "required": True,
            },
            {
                "type": 3,
                "name": "item",
                "description": 'The item to redeem. Can be a pokemon name or "credits".',
                "required": True,
            },
        ],
    },
    {
        "id": "888887921208328193",
        "application_id": "519850436899897346",
        "version": "888887921208328194",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "auto",
        "description": "Have the bot automatically perform certain actions on spawns.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "delete",
                "description": "Toggle the bot automatically deleting spawns.",
            },
            {
                "type": 1,
                "name": "pin",
                "description": "Toggle the bot automatically pinning rare spawns.",
            },
        ],
    },
    {
        "id": "888887930230308895",
        "application_id": "519850436899897346",
        "version": "986062794216599582",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "redirect",
        "description": "Redirect spawns to specific channels.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "add",
                "description": "Add a channel for spawns to be redirected to.",
                "options": [
                    {
                        "type": 7,
                        "name": "channel",
                        "description": "The channel to add. If not provided, the current channel will be used.",
                        "channel_types": [0],
                    }
                ],
            },
            {
                "type": 1,
                "name": "remove",
                "description": "Remove a channel from the spawn redirection list.",
                "options": [
                    {
                        "type": 7,
                        "name": "channel",
                        "description": "The channel to remove. If not provided, the current channel will be used.",
                    }
                ],
            },
            {
                "type": 1,
                "name": "clear",
                "description": "Clear the spawn redirection list.",
            },
        ],
    },
    {
        "id": "888887939801710632",
        "application_id": "519850436899897346",
        "version": "888887939801710633",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "commands",
        "description": "Set whether commands can be used in a channel.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "disable",
                "description": "Disable commands in a channel.",
                "options": [
                    {
                        "type": 7,
                        "name": "channel",
                        "description": "The channel to disable commands in. If not provided, the current channel will be used.",
                    }
                ],
            },
            {
                "type": 1,
                "name": "enable",
                "description": "Enable commands in a channel.",
                "options": [
                    {
                        "type": 7,
                        "name": "channel",
                        "description": "The channel to enable commands in. If not provided, the current channel will be used.",
                    }
                ],
            },
        ],
    },
    {
        "id": "888887948882350100",
        "application_id": "519850436899897346",
        "version": "978906602964926474",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "spawns",
        "description": "Set whether pokemon can spawn in a channel.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "disable",
                "description": "Disable spawns in a channel.",
                "options": [
                    {
                        "type": 7,
                        "name": "channel",
                        "description": "The channel to disable spawns in. If not provided, the current channel will be used.",
                    }
                ],
            },
            {
                "type": 1,
                "name": "enable",
                "description": "Enable spawns in a channel.",
                "options": [
                    {
                        "type": 7,
                        "name": "channel",
                        "description": "The channel to enable spawns in. If not provided, the current channel will be used.",
                    }
                ],
            },
            {
                "type": 1,
                "name": "small",
                "description": "Toggle whether spawns should use small images.",
            },
            {
                "type": 1,
                "name": "check",
                "description": "Check what channels in your server can spawn pokemon.",
            },
        ],
    },
    {
        "id": "888887996877787186",
        "application_id": "519850436899897346",
        "version": "888887996877787187",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "shop",
        "description": "View items in the shop.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "shop",
                "description": "The shop to view. Leave blank to view the shops.",
            }
        ],
    },
    {
        "id": "888888006105255936",
        "application_id": "519850436899897346",
        "version": "888888006105255937",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "start",
        "description": "Start your pokemon journey!",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "starter",
                "description": "Your starter pokemon. Leave blank to view starter options.",
            }
        ],
    },
    {
        "id": "888888015110406234",
        "application_id": "519850436899897346",
        "version": "973386126062649355",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "gift",
        "description": "Gift something to another user.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "credits",
                "description": "Gift credits to another user.",
                "options": [
                    {
                        "type": 6,
                        "name": "user",
                        "description": "The user to give credits to.",
                        "required": True,
                    },
                    {
                        "type": 4,
                        "name": "amount",
                        "description": "The amount of credits to give.",
                        "required": True,
                    },
                ],
            },
            {
                "type": 1,
                "name": "redeems",
                "description": "Gift redeems to another user.",
                "options": [
                    {
                        "type": 6,
                        "name": "user",
                        "description": "The user to give redeems to.",
                        "required": True,
                    },
                    {
                        "type": 4,
                        "name": "amount",
                        "description": "The amount of redeems to give.",
                        "required": True,
                    },
                ],
            },
            {
                "type": 1,
                "name": "pokemon",
                "description": "Gift pokemon to another user.",
                "options": [
                    {
                        "type": 6,
                        "name": "user",
                        "description": "The user to give pokemon to.",
                        "required": True,
                    },
                    {
                        "type": 4,
                        "name": "poke",
                        "description": "The pokemon to give.",
                        "required": True,
                    },
                ],
            },
        ],
    },
    {
        "id": "888888033024278590",
        "application_id": "519850436899897346",
        "version": "888888033024278591",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "trade",
        "description": "Start an interactive trade with another user.",
        "dm_permission": True,
        "options": [
            {
                "type": 6,
                "name": "user",
                "description": "The user to trade with.",
                "required": True,
            }
        ],
    },
    {
        "id": "888888081321701396",
        "application_id": "519850436899897346",
        "version": "888888081321701397",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "tutorial",
        "description": "View a tutorial to get you started with Mewbot.",
        "dm_permission": True,
    },
    {
        "id": "898791120887222322",
        "application_id": "519850436899897346",
        "version": "984622160586879016",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "lookup",
        "description": "Lookup data on pokemon.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "move",
                "description": "Lookup information on a move.",
                "options": [
                    {
                        "type": 3,
                        "name": "move",
                        "description": "The move to get data about.",
                        "required": True,
                    }
                ],
            },
            {
                "type": 1,
                "name": "ability",
                "description": "Lookup information on an ability.",
                "options": [
                    {
                        "type": 3,
                        "name": "ability",
                        "description": "The ability to get data about.",
                        "required": True,
                    }
                ],
            },
            {
                "type": 1,
                "name": "type",
                "description": "Lookup information on a type.",
                "options": [
                    {
                        "type": 3,
                        "name": "type",
                        "description": "The primary type to get data about.",
                        "required": True,
                    },
                    {
                        "type": 3,
                        "name": "type2",
                        "description": "The second type of a duel-type pokemon.",
                    },
                ],
            },
        ],
    },
    {
        "id": "904107767420305458",
        "application_id": "519850436899897346",
        "version": "904107767420305459",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 2,
        "name": "Trade",
        "description": "",
        "dm_permission": True,
    },
    {
        "id": "905984466613317713",
        "application_id": "519850436899897346",
        "version": "907032920248705086",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "sell",
        "description": "Sell different things.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "item",
                "description": "Sell an item from your bag.",
                "options": [
                    {
                        "type": 3,
                        "name": "item",
                        "description": "The name of the item you'd like to sell.",
                        "required": True,
                    },
                    {
                        "type": 4,
                        "name": "amount",
                        "description": "The amount you'd like to sell. Defaults to 1.",
                    },
                ],
            },
            {
                "type": 1,
                "name": "egg",
                "description": "Sell an egg.",
                "options": [
                    {
                        "type": 3,
                        "name": "num",
                        "description": 'The egg\'s number, or "new".',
                        "required": True,
                    }
                ],
            },
        ],
    },
    {
        "id": "909222963453239306",
        "application_id": "519850436899897346",
        "version": "994414999839723520",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "skin",
        "description": "Manage your pokemon skins.",
        "dm_permission": True,
        "options": [
            {
                "type": 1,
                "name": "apply",
                "description": "Apply a skin to a pokemon.",
                "options": [
                    {
                        "type": 4,
                        "name": "poke",
                        "description": "The pokemon number to add the skin to.",
                        "required": True,
                    },
                    {
                        "type": 3,
                        "name": "skin",
                        "description": "The name of the skin to apply.",
                        "required": True,
                    },
                ],
            },
            {"type": 1, "name": "list", "description": "View your owned skins."},
            {
                "type": 1,
                "name": "preview",
                "description": "Preview one of your skins.",
                "options": [
                    {
                        "type": 3,
                        "name": "poke",
                        "description": "The pokemon name the skin is for.",
                        "required": True,
                    },
                    {
                        "type": 3,
                        "name": "skin",
                        "description": "The name of the skin to preview.",
                        "required": True,
                    },
                ],
            },
            {
                "type": 1,
                "name": "shop",
                "description": "View the skins available to you for purchase this week.",
            },
            {
                "type": 1,
                "name": "buy",
                "description": "Buy a skin from your shop with skin shards.",
                "options": [
                    {
                        "type": 3,
                        "name": "poke",
                        "description": "The pokemon name to buy the skin for.",
                        "required": True,
                    },
                    {
                        "type": 3,
                        "name": "skin",
                        "description": "The name of the skin to buy.",
                        "required": True,
                    },
                ],
            },
        ],
    },
    {
        "id": "929907140175466536",
        "application_id": "519850436899897346",
        "version": "929907140175466537",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "leaderboard",
        "description": "View various leaderboards for mewbot.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "board",
                "description": "The leaderboard to view.",
                "required": True,
                "choices": [
                    {"name": "Votes", "value": "vote"},
                    {"name": "Servers", "value": "servers"},
                    {"name": "Pokemon", "value": "pokemon"},
                    {"name": "Fishing", "value": "fishing"},
                ],
            }
        ],
    },
    {
        "id": "942263278636269599",
        "application_id": "519850436899897346",
        "version": "949423115786670110",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "region",
        "description": "Change your region to make your pokes evolve into regional forms.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "region",
                "description": "The region to enter.",
                "required": True,
                "choices": [
                    {"name": "Original", "value": "original"},
                    {"name": "Alola", "value": "alola"},
                    {"name": "Galar", "value": "galar"},
                    {"name": "Hisui", "value": "hisui"},
                ],
            }
        ],
    },
    {
        "id": "954958501552205884",
        "application_id": "519850436899897346",
        "version": "954958501552205885",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "hunt",
        "description": "Select a pokemon to shadow hunt for, giving a chance to get a shadow skin for it.",
        "dm_permission": True,
        "options": [
            {
                "type": 3,
                "name": "poke",
                "description": "The pokemon to hunt for.",
                "required": True,
            }
        ],
    },
    {
        "id": "965414871514619964",
        "application_id": "519850436899897346",
        "version": "965414871514619965",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "help",
        "description": "View a tutorial to get you started with Mewbot.",
        "dm_permission": True,
    },
    {
        "id": "966039777856061450",
        "application_id": "519850436899897346",
        "version": "966039777856061451",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "cooldowns",
        "description": "View the breeding cooldowns for your pokemon.",
        "dm_permission": True,
    },
    {
        "id": "974392582815760434",
        "application_id": "519850436899897346",
        "version": "974392582815760435",
        "default_permission": True,
        "default_member_permissions": None,
        "type": 1,
        "name": "resetme",
        "description": "Reset your account, losing all data including pokemon. Cannot be undone.",
        "dm_permission": True,
    },
]
