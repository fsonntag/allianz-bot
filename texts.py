# coding=utf-8

car = [
    u"You're looking for a car insurance, we have the following options for you:"
]

detailed_insurance = [
    lambda name: u"%s got you covered. Here are our conditions:" % name
]

extended_detailed_insurance = [
    lambda name: u"The extended %s got you covered in any. Here are the conditions:" % name
]

offer_extended = [
    u"There's also an extended version, in case you want to know about it."
]

quote = [
    lambda url: u"Sure! Here you go: %s" % url,
    lambda url: u"Definitely! %s" % url
]

available = [
    "We got the following types of insurances. Which ones are you interested in?"
]

bye = [
    "Catch you later!",
    "Bye!",
    "Have a nice day!",
    "Cheersy"
]
