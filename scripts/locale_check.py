# -*- coding: utf-8 -*-
import json
import urllib

"""This script helps you to check if a Tuxemon translation is correct."""


def getJSON(url):
    """Get the JSON file in a dict format.

    A valid JSON url must be provided in order to work."""
    response = urllib.urlopen(url)
    return json.loads(response.read())


def getLanguages():
    """Get the list of available languages on the development repo of Tuxemon.

    It parses files in the locale directory and removes the json extension.
    The function works with getJSON function."""
    languages = []
    url = "https://api.github.com/repos/Tuxemon/Tuxemon/contents/tuxemon/resources/db/locale"
    languagesJSON = getJSON(url)
    for l in range(len(languagesJSON)):
        if languagesJSON[l]["name"][-5:] == ".json":
            languages.append(languagesJSON[l]["name"][:-5])
    languages.sort()
    return languages


def setOrigTransLanguages(languages):
    """Set the keys of two valid language codes.

    The first one is for the original source
    and the second one for the translation.
    A valid languages vector must be provided.
    It is returned by getLanguages function."""
    print "Choose between these options:"
    for l in range(len(languages)):
        print "- " + languages[l]
    langTrans = raw_input("Type the language code of the translation: ")
    while langTrans not in languages:
        print "Not recognized input."
        langTrans = raw_input("Type the language code of the translation: ")
    langOrig = raw_input("Type the language code of the original source: ")
    while langOrig not in languages:
        print "Not recognized input."
        langOrig = raw_input("Type the language code of the original source: ")
    return langOrig, langTrans


def getOrigTransJSONs(langOrig, langTrans):
    """Get the JSON file in a dict format of original source and translation.

    The function needs two valid language codes as input,
    one for the source language and one for the translation one.
    The function works with getJSON function."""
    url = "https://raw.githubusercontent.com/Tuxemon/Tuxemon/development/tuxemon/resources/db/locale/"
    langOrigKeys = getJSON(url + langOrig + ".json")
    langTransKeys = getJSON(url + langTrans + ".json")
    return langOrigKeys, langTransKeys


def checkEmptyKeys(langOrig, langTrans):
    """Check if a key is present and empty in the translation, while in the source has been translated.

    It means that a new translation must be provided in order to be updated.
    The function works with getOrigTransJSONs function."""
    emptyKeys = []
    langOrigKeys, langTransKeys = getOrigTransJSONs(langOrig, langTrans)
    for key in langOrigKeys.keys():
        if langOrigKeys[key] != "" and key in langTransKeys and langTransKeys[key] == "":
            emptyKeys.append(key)
    if len(emptyKeys) == 0:
        print "No empty keys found!"
    else:
        print "The following keys are present but empty:"
        emptyKeys.sort()
        for key in emptyKeys:
            print "- " + key


def checkCopiedKeys(langOrig, langTrans, checkTuxemonName, checkPeopleName):
    """Check if a key in the original source and in the translation is the same.

    It may contain many false positives because the sentence in the original
    source and in the translation is really equal.
    Check the result in order to find out if somebody copy-pasted a key
    in the original source and forgot to translate it.
    The function works with getOrigTransJSONs function."""
    copiedKeys = []
    peopleNames = ["npc_maple_name", "npc_wife"]
    langOrigKeys, langTransKeys = getOrigTransJSONs(langOrig, langTrans)
    for key in langOrigKeys.keys():
        if checkTuxemonName == "False" and (key.split("_")[0] == "txmn" and key.split("_")[-1] == "name"):
            print "KEY FOUND: " + key
            del langOrigKeys[key]
        if checkPeopleName == "False" and key in peopleNames:
            print "KEY FOUND: " + key
            del langOrigKeys[key]
    for key in langOrigKeys.keys():
        if key in langTransKeys and langOrigKeys[key] == langTransKeys[key] and langOrigKeys != "":
            copiedKeys.append(key)
    if len(copiedKeys) == 0:
        print "No copied keys found!"
    else:
        print "The following keys must be checked:"
        copiedKeys.sort()
        for key in copiedKeys:
            print "- " + key + " (orig: \"" + langOrigKeys[key] + "\", trans: \"" + langTransKeys[key] + "\")"


def checkNoMoreExistingKeys(langOrig, langTrans):
    """Check if a key is present in the translation but not in the source.

    It means that either the translation is more updated than the source
    or the name of the keys changed and an update is needed."""
    noMoreExistingKeys = []
    langOrigKeys, langTransKeys = getOrigTransJSONs(langOrig, langTrans)

    for key in langTransKeys.keys():
        if key not in langOrigKeys:
            noMoreExistingKeys.append(key)
    if len(noMoreExistingKeys) == 0:
        print "No non-existing keys found!"
    else:
        print "The following keys must be checked:"
        noMoreExistingKeys.sort()
        for key in noMoreExistingKeys:
            print "- " + key


def checkCategoryKeys(langOrig, langTrans):
    """Check if a category is translated in different ways.

    It means that maybe the translation should be uniform between these keys."""

    langOrigKeys, langTransKeys = getOrigTransJSONs(langOrig, langTrans)
    alreadyDone = []
    diffKeys = {}

    for key in langOrigKeys.keys():
        if key.split("_")[0] == "txmn" and key.split("_")[-1] == "category" and langOrigKeys[key] not in alreadyDone:
            trigger = 0
            samecategory = []
            cat = langOrigKeys[key]
            alreadyDone.append(cat)
            for key2 in langOrigKeys.keys():
                if langOrigKeys[key2] == cat:
                    samecategory.append(key2)
            for keyTrans in samecategory:
                for keyTrans2 in samecategory:
                    if keyTrans in langTransKeys.keys() and keyTrans2 in langTransKeys.keys() and langTransKeys[keyTrans] != langTransKeys[keyTrans2]:
                        trigger = 1
            if trigger == 1:
                diffKeys[cat] = samecategory
    if len(diffKeys) == 0:
        print "Everything is okay!"
    else:
        print "The following keys must be checked:"
        keys = diffKeys.keys()
        keys.sort()
        for key in keys:
            print "\"" + key + "\":"
            for i in range(len(diffKeys[key])):
                print "- \"" + diffKeys[key][i] + "\""


if __name__ == "__main__":
    loop = True
    while loop:
        print "Please, select an option:"
        print "1. Look for empty keys"
        print "2. Look for copied and not translated keys (not working)"
        print "3. Look for keys not existing anymore"
        print "4. Look for Tuxemon categories with different translations"
        print "e. Exit"
        choice = raw_input("Option: ")
        if choice == "1":
            languages = getLanguages()
            langOrig, langTrans = setOrigTransLanguages(languages)
            checkEmptyKeys(langOrig, langTrans)

        elif choice == "2":
            languages = getLanguages()
            langOrig, langTrans = setOrigTransLanguages(languages)
            print "Do you want to check also..."
            checkTuxemonName = raw_input("...Tuxemon names? (Y, N): ")
            while checkTuxemonName not in ["y", "Y", "yes", "n", "N", "no"]:
                print "Not recognized input."
                print "Do you want to check also..."
                checkTuxemonName = raw_input("...Tuxemon names? (Y, N): ")
            if checkTuxemonName in ["y", "Y", "yes"]:
                checkTuxemonName = True
            else:
                checkTuxemonName = False
            checkPeopleName = raw_input("... names of NPCs? (Y, N): ")
            while checkPeopleName not in ["y", "Y", "yes", "n", "N", "no"]:
                print "Not recognized input."
                print "Do you want to check also..."
                checkPeopleName = raw_input("... names of NPCs? (Y, N): ")
            if checkPeopleName in ["y", "Y", "yes"]:
                checkPeopleName = True
            else:
                checkPeopleName = False
            checkCopiedKeys(langOrig, langTrans,
                            checkTuxemonName, checkPeopleName)

        elif choice == "3":
            languages = getLanguages()
            langOrig, langTrans = setOrigTransLanguages(languages)
            checkNoMoreExistingKeys(langOrig, langTrans)

        elif choice == "4":
            languages = getLanguages()
            langOrig, langTrans = setOrigTransLanguages(languages)
            checkCategoryKeys(langOrig, langTrans)
        elif choice == "e":
            print "Goobye and don't forget to spread Tuxemon game!"
            loop = False
        else:
            print "Your choice is wrong."
