#!/usr/bin/env python2
# -*- coding: utf-8 -*

import nltk
import itertools
import numpy as np
import re
import sys
import codecs
import yaml

from parse import load_data, PROJECT
from readability.readability import ReadabilityTool

from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures
from nltk.tokenize import sent_tokenize
from nltk.tokenize import TreebankWordTokenizer
from nltk.stem import WordNetLemmatizer

from dict_vectorizer import DictVectorizer
#from sklearn.feature_extraction import DictVectorizer
#from sklearn.feature_extraction.text import strip_accents_unicode

# learning and k-fold cv
from sklearn.linear_model import LogisticRegression
from sklearn import metrics
from sklearn import cross_validation

PRINT_COEFS = False
PRINT_ERRORS = True

http_re = re.compile(r"((http|ftp|https):\/\/)?[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?", re.IGNORECASE)
oddities_re = re.compile(ur"(=|¡¿|·|\\|\^|~|…|“|”|ß|€)")
tokenize2_re = re.compile(r"(\w+)([-.\\/])+", re.UNICODE)
phonenumber_re = re.compile(r"(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})")
haha_re = re.compile(r"[ah]{4,20}", re.IGNORECASE)
plain_number_re = re.compile(r"-?\d{2,7}(([,\.])\d{2,7})*")
money_number_re = re.compile(r"[$€]-?\d{2,7}(([,\.])\d{2,7})*", re.UNICODE)
smiley_re = re.compile(r"((?::|;|=)(?:-)?(?:\)|D|P))")
swastika = u"卐"

# Wordlists
bad_words = set([line.strip().lower() for line in open(PROJECT + 'corp/badwords-adult.txt')])
reveal_words = yaml.load(open(PROJECT + 'corp/word_list_dirty_words/reveal_questionable_words.yaml').read())[0]['dataset']['payload'][0]['word_list']
hate_words = set([x['word'].lower() for x in reveal_words if x['category'] == 'hate'])
drug_words = set([x['word'].lower() for x in reveal_words if x['category'] == 'drug'])
cult_words = set([x['word'].lower() for x in reveal_words if x['category'] == 'cult'])
occult_words = set([x['word'].lower() for x in reveal_words if x['category'] == 'occult'])
porn_words = set([x['word'].lower() for x in reveal_words if x['category'] == 'pornographic'])
fwenzel_words = set([word for word in open(PROJECT + 'corp/word_list_dirty_words/word_list-fwenzel_reporter.txt').read().split("\n") if len(word.split()) == 1])
english_vocab = set(w.lower() for w in nltk.corpus.words.words())

# Tokenizers
wordtokenizer = TreebankWordTokenizer()
wnl = WordNetLemmatizer()
ps = nltk.stem.PorterStemmer()

def numrepl(m):
    try:
        x = m.group(0)
        if u"$" in x or u"€" in x:
            return " moneynumber "
        x = x.replace(",", "")
        x = x.replace(".", "")
        x = int(x)

        if 1950 <= x <= 2015:
            return " year "
        elif x < x < 50:
            return " smallnumber "
        elif x == 0:
            return " zeronumber "
        elif x < 0:
            return " negativenumber "
        elif x in [10, 100, 500, 1000, 10000, 100000]:
            return " %d " % x
        else:
            return " othernumber "
    except Exception, e:
        return " errornumber "

def parse_text(text):
    text = text.replace("_", " ").replace("\r\n", " NL2 ").replace("\n", " NL ") \
            .replace("\'", "'").replace(u"\xc2\xa0", " NBSP ") \
            .replace(u"\xa0", " NBSP2 ")

    text = text.replace(u"\xe2\x80\x98", "'")
    text = text.replace(u"\xe2\x80\x99", "'")
    text = text.replace(u"\xe2\x80\x9c", "\"")
    text = text.replace(u"\xe2\x80\x9d", "\"")
    text = text.replace(u"\xe2\x80\x93", "-")
    text = text.replace(u"\xe2\x80\x94", "--")
    text = text.replace(u"\xe2\x80\xa6", "...")

    text = text.replace(u"\ufeff", " ")

# TODO: this might be faster
#    text = strip_accents_unicode(text)

    text = text.replace(u"’", "'")
    text = text.replace(u"`", "'")

    text = http_re.sub(" dummyhtml ", text)
    text = phonenumber_re.sub(" dummyphone ", text)
#    text = dotdot_re.sub(lambda m: "%s %s %s" % (m.group(1), m.group(2), m.group(4)), text)

    text = money_number_re.sub(numrepl, text)
    text = plain_number_re.sub(numrepl, text)

    text = smiley_re.sub(" smiley ", text)
    text = haha_re.sub(" haha ", text)

    text = oddities_re.sub(lambda m: " %s " % m.group(1), text)
    text = tokenize2_re.sub(lambda m: "%s %s " % (m.group(1), m.group(2)), text)
    return text

def create_features(X, user_data = None):
    res = []

    for date, comment, user in X:
        feat = {}
        has_hate_word = has_drug_word = has_cult_word = has_occult_word = has_porn_word = 0
        has_fwenzel_word = 0
        has_swastika = swastika in comment

        comment = comment.lower()


        comment = parse_text(comment)
       
        comment = nltk.clean_html(comment)

        sents = sent_tokenize(comment)
        doc = []
        for sent in sents:
            # Tokenize each sentence.
            doc += wordtokenizer.tokenize(sent)
        def repl_filter(x):
            return x.lower() not in ["nl", "nl2", "nbsp", "nbsp2", "dummyhtml"]

        # Remove stopwords and replacement tokens.
        doc = filter(repl_filter, doc)

        for i, word in enumerate(doc):
            if doc[i] in bad_words:
                doc[i] = '_badword_'

            doc[i] = ps.stem(doc[i])

            doc[i] = wnl.lemmatize(doc[i])

            if doc[i] in bad_words:
                doc[i] = '_badword_'

            if doc[i] in hate_words:
                has_hate_word = 1
            if doc[i] in drug_words:
                has_drug_word = 1
            if doc[i] in cult_words:
                has_cult_word = 1
            if doc[i] in occult_words:
                has_occult_word = 1
            if doc[i] in porn_words:
                has_porn_word = 1
            if doc[i] in fwenzel_words:
                has_fwenzel_word = 1

        bigram_finder = BigramCollocationFinder.from_words(doc)
        bigrams = bigram_finder.nbest(BigramAssocMeasures.chi_sq, n=5)

        bigram = dict([(ngram, True) for ngram in itertools.chain(doc, bigrams)])

        feat.update(bigram)

        text_vocab = set(w for w in doc if w.isalpha())
        unusual = text_vocab.difference(english_vocab)
        unusual_ratio = len(unusual) / len(text_vocab) if len(text_vocab) != 0 else -1.0

        unusual2 = unusual.difference(set("_badword_"))
        unusual_ratio2 = len(unusual2) / len(text_vocab) if len(text_vocab) != 0 else -1.0


        if user_data is not None:
            user_info = user_data[user]

        has_bad_word = True
        for word in bad_words:
            if word in comment.lower():
                break
        else:
            has_bad_word = False

        def n_none(x):
            return int(x) if x is not None else 0
        def c_none(x):
            return x if x is not None else "__None__"

        readability = ReadabilityTool(comment)

        read_feat = {}
        for f, val in readability.analyzedVars.items():
            if f != 'words':
                read_feat["_" + f] = val
        for test, val in readability.tests_given_lang['eng'].items():
            read_feat["__" + test] = val(readability.text)

        feat['_always_present'] = True
        feat['_word_num'] = len(doc)
        feat['_sent_num'] = len(sents)
        feat['_word_var'] = len(set(doc)) / len(doc) if len(doc) != 0 else -1.0
        feat['_sent_var'] = len(set(sents)) / len(sents)
        feat['_unusual_ratio'] = unusual_ratio
        feat['_unusual_ratio2'] = unusual_ratio2
        if user_data is not None:
            feat['_username'] = user
            feat['_user_subcount'] = int(user_info['SubscriberCount'])
            feat['_user_friends'] = int(user_info['FriendsAdded'])
            feat['_user_favs'] = int(user_info['VideosFavourited'])
            feat['_user_videorates'] = int(user_info['VideosRated'])
            feat['_user_videouploads'] = int(user_info['VideosUploaded'])
            feat['_user_videocomments'] = int(user_info['VideosCommented'])
            feat['_user_videoshares'] = int(user_info['VideosShared'])
            feat['_user_usersubs'] = int(user_info['UserSubscriptionsAdded'])
            feat['_user_gender'] =  c_none(user_info['Gender'])
            feat['_user_age'] =  n_none(user_info['Age'])
            feat['_user_closed'] = user_info['UserAccountClosed']
            feat['_user_suspended'] = user_info['UserAccountSuspended']
            feat['_user_has_gender'] = 1 if user_info['Gender'] is not None else 0
            feat['_user_has_school'] = 1 if user_info['School'] is not None else 0
            feat['_user_has_books'] = 1 if user_info['Books'] is not None else 0
            feat['_user_has_movies'] = 1 if user_info['Movies'] is not None else 0
            feat['_user_has_music'] = 1 if user_info['Music'] is not None else 0
            feat['_user_has_location'] = 1 if user_info['Location'] is not None else 0
            feat['_user_has_hometown'] = 1 if user_info['Hometown'] is not None else 0
    #        feat['_user_last'] = user_info['LastWebAccess']

    # Dictionary features
        feat['_has_bad_word'] = has_bad_word
#        feat['_has_hate_word'] = has_hate_word
#        feat['_has_drug_word'] = has_drug_word
        feat['_has_cult_word'] = has_cult_word
        feat['_has_swastika'] = has_swastika
#        feat['_has_occult_word'] = has_occult_word
#        feat['_has_has_fwenzel_word'] = has_fwenzel_word
        feat['_has_porn_word'] = has_porn_word
        feat['_has_swastika'] = has_swastika
        feat.update(read_feat)

#        print feat
        res.append(feat)
    return res

def kfold_run((i, k, cls, train_X, train_y, test_X, test_y)):
    print "Training on fold #%d/%d" % (i + 1, k)
    cls.fit(train_X, train_y)
    return cls.score(test_X, test_y)

def main():
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)

    res = kfold(10)

def kfold(k=10):
    print "Loading data."
    videos, users, reviews = load_data()

    print "Extracting features."
    orig_X = np.array([(x['date'], x['text'], x['user']) for x in reviews])
    feats = create_features(orig_X, users)
    #y = np.array([1 if x['spam'] == 'true' else 0 for x in reviews])
    y = np.array([1 if x['adult'] == 'true' else 0 for x in reviews])

    print "Vectorizing features."
    v = DictVectorizer(sparse=False)
    feats = v.fit_transform(feats)

    print "Starting K-fold cross validation."
    cv = cross_validation.KFold(len(feats), k=k, indices=True, shuffle=True, random_state=1234)

    cls = LogisticRegression(penalty='l2', tol=0.00001, fit_intercept=False, dual=False, C=2.4105, class_weight=None)
    if PRINT_COEFS:
        cls.fit(feats, y)
        c = v.inverse_transform(cls.coef_)
        for key, val in sorted(c[0].iteritems(), key=lambda x: x[1]):
#            if isinstance(key, str) and key.startswith("_"):
             print key, val
        quit()

    sumoi = 0
    sumprec = 0
    sumrec = 0
    f1sum = 0

    for i, (train_idx, test_idx) in enumerate(cv):
        train_X, train_y, test_X, test_y = feats[train_idx], \
                y[train_idx], feats[test_idx], y[test_idx]
        cls.fit(train_X, train_y)
        preds = cls.predict(test_X)

        if PRINT_ERRORS:
#            worst = np.argsort(np.abs(test_y - preds))
            #for j in worst[-1:-10:-1]:
            orig_test = orig_X[test_idx]
#            for j in worst:
            for j in range(len(orig_test)):
                if test_y[j] != preds[j]:
                    print j, orig_test[j][1], test_y[j], preds[j]
            #quit()

        oi = metrics.zero_one_score(test_y, preds)
	prec = metrics.precision_score(test_y, preds)
	rec = metrics.recall_score(test_y, preds)
	f1 = metrics.f1_score(test_y, preds)

#        print "Fold %d F1 score: %.5f" % (i, f1)
	print "Fold %d 01: %.5f Prec: %.5f Rec: %.5f F1: %.5f" % (i, oi, prec, rec, f1)
        sumoi += oi
	sumprec += prec
	sumrec += rec
	f1sum += f1

    avgf1 = (f1sum / k)
#    print "Mean F1 score: %.5f" % (f1sum / k)
    print "Mean 01: %.5f Prec: %.5f Rec: %.5f F1: %.5f" % (sumoi/k, sumprec/k, sumrec/k, f1sum/k)

#    scores = cross_validation.cross_val_score(cls, feats, y, cv=10, score_func=metrics.f1_score)
#    for i, score in enumerate(scores):
#        print "Fold %d: %.5f" % (i, score)
#    print "Mean score: %0.5f (+/- %0.2f)" % (scores.mean(), scores.std() / 2)

    return avgf1

if __name__ == "__main__":
    main()
