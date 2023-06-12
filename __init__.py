from aqt import mw
from aqt.utils import showInfo
from aqt.qt import *
from anki.consts import *


def isKanji(text):
    return ord(text) >= 0x4e00 and ord(text) < 0xa000

def getUniqueKanji(text):
    kanjiSet = set()
    for line in text:
        for c in line:
            if isKanji(c):
                kanjiSet.add(c)
    return kanjiSet

def summarizeNote(note):
    maxLen = 50
    s = note.joinedFields()
    if len(s) < maxLen:
        return s
    else:
        return s[:maxLen] + "..."

def summarizeKanji(kanji):
    s = ''.join(sorted(kanji))
    maxLen = 50
    if len(s) < maxLen:
        return s
    else:
        return s[:maxLen] + "[...%d more...]" % (len(s) - maxLen)

def summarizeList(l):
    maximum = 20
    if len(l) < maximum:
        return l
    else:
        l2 = l[:maximum]
        l2.append('[...%d more...]' % (len(l) - maximum))
        return l2

def getDeckNotes(deckName, filt=''):
    return mw.col.findNotes('deck:"%s" %s' % (deckName, filt))

# Returns all kanji in the "review" phase
def getKnownKanji(deckName, kanjiField):
    kanjiSet = set()

    if len(getDeckNotes(deckName)) == 0:
        infoString = """
Deck '%s' is empty or does not exist. Try changing the value of 'kanji_deck_name' in addon config.<br><br>
Note: if the deck is nested in another deck then the full name is necessary. ie. if a deck named \"Kanji\"
is nested under a deck called \"Japanese\", then the full name would be \"Japanese::Kanji\".
"""

        showInfo(infoString % deckName, type='critical')
        return None

    noteList = getDeckNotes(deckName, 'is:review')
    for noteid in noteList:
        note = mw.col.getNote(noteid)
        if kanjiField in note:
            for k in getUniqueKanji(note[kanjiField]):
                kanjiSet.add(k)
        else:
            showInfo("Field '%s' not found in deck '%s'. Try changing the value of 'kanji_deck_field' in addon config." % (kanjiField, deckName), type='critical')
            return None
    return kanjiSet

def ignoreNote(note):
    joinedFields = note.joinedFields()
    if not any(isKanji(k) for k in joinedFields):
        return True
    return False

def getConfig(name):
    return mw.addonManager.getConfig(__name__).get(name)

def updateManagedCards():
    cardType = getConfig('card_type')
    sorting = getConfig('decending')
    extra = getConfig('extra_search_param')
    kanjiField = getConfig('kanji_deck_field')
    deckName = getConfig('kanji_deck_name')
    sortField = getConfig('sort_field')
    sortField2 = getConfig('sort_field2')
    sortField3 = getConfig('sort_field3')
    wordField = getConfig('word_field')
    wordLimit = getConfig('word_limit')
    

    knownKanji = getKnownKanji(deckName, kanjiField)

    if knownKanji == None:
        return

    suspendedText = []
    unsuspendedText = []
    for ki in knownKanji:
        results = []
        managedCards = mw.col.findCards('%s:*%s* card:%s %s' % (wordField, ki, cardType, extra))
        for cardid in managedCards:
            card = mw.col.getCard(cardid)
            note = card.note()
            if note[sortField] != '':
                order=float(note[sortField])
            elif note[sortField2] != '':
                order=2*float(note[sortField2])
            elif note[sortField3] != '':
                order=3*float(note[sortField3])
            else:
                order=999999
            results.append([order, cardid])
        if len(managedCards) > 0:
            sresults=sorted(results,key=lambda l:l[0], reverse=sorting) 
            for wi in range(wordLimit):
                card = mw.col.getCard(sresults[wi][1])
                note = card.note()
                note.addTag("kanji_top_nth_words")
                note.flush()
                # if card.queue == -1:
                #     note.addTag("kanji_top_nth_words_unsuspended")
                #     note.flush()
                #     mw.col.sched.unsuspendCards([sresults[wi][1]])
                #     unsuspendedText.append('%s; ' % (summarizeNote(note)))
                    

    if len(suspendedText) == 0:
        suspendedText = ['None']
    if len(unsuspendedText) == 0:
        unsuspendedText = ['None']

    knownKanjiString = '<b>Known Kanji:</b> ' + summarizeKanji(knownKanji) + '<br><br>'
    unsuspendedCardString = 'Tagged cards:</b><br>%s<br>' % '<br>'.join(summarizeList(unsuspendedText))
    showInfo(knownKanjiString + unsuspendedCardString)

# Menu item
action = QAction("Tag Kanji Top Nth Words", mw)
action.triggered.connect(updateManagedCards)
mw.form.menuTools.addAction(action)
