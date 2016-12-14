import pandas as pd
import numpy as np
from string import punctuation
import re
import dill as pickle
from time import time
from datetime import datetime
from unidecode import unidecode

from sklearn.feature_extraction.text import TfidfVectorizer, TfidfTransformer, CountVectorizer
from sklearn.decomposition import NMF

import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
from nltk.stem.wordnet import WordNetLemmatizer


class TopicModeling(object):

    def __init__(self):
        pass


    def clean_documents(self, descriptions):
        documents = [unidecode(document).lower().translate(None, string.punctuation)
                    for document in descriptions]
        documents = [re.sub(r'\d+', '', doc) for doc in documents]
        return documents


    def get_tf(self, descriptions):
        '''
        INPUT: array of project descriptions
        OUTPUT: count_vectorizer, term_frequency_matrix
        '''
        documents = self.clean_documents(descriptions)
        countvec = CountVectorizer(stop_words='english', tokenizer=word_tokenize,
                   min_df=5, max_df =0.95 ,ngram_range=(1, 2),
                   preprocessor=PorterStemmer().stem)
        word_counts_matrix = countvec.fit_transform(documents)

        return countvec, word_counts_matrix


    def get_tfidf(self, descriptions):
        '''
        INPUT: array of project descriptions
        OUTPUT: tfidf_vectorizer, tfidf_matrix
        '''
        documents = self.clean_documents(descriptions)
        tfidfvec = TfidfVectorizer(stop_words='english', tokenizer=word_tokenize,
                   min_df=5, max_df =0.95 ,ngram_range=(1, 2),
                   preprocessor=PorterStemmer().stem)
        tfidf_matrix = tfidfvec.fit_transform(documents)

        return tfidfvec, tfidf_matrix


    def get_nmf_results(self, tfidf_matrix, n_topics=20):
        '''
        INPUT: tfidf_matrix, number of latent topics
        OUTPUT: W matrix, H matrix, nmf
        '''
        nmf = NMF(n_components=n_topics)
        W = nmf.fit_transform(tfidf_matrix)
        H = nmf.components_

        return W, H, nmf


    def get_Wtest(self, full_tf, X_test_d, nmf):
        full_tf_matrix_test = full_tf.transform(X_test_d)
        W_test = nmf.transform(full_tf_matrix_test)

        return W_test, full_tf_matrix_test


    def get_success_pct_per_topic(W,y):
        '''
        Retrieve campaign success percentage by latent topics.
        INPUT: W matrix, y array
        OUTPUT: dataframe of topics and success percentage
        '''
        topic_label = np.apply_along_axis(func1d=np.argmax,axis=1, arr=W)
        dtf = pd.DataFrame()
        dtf['topic'] = topic_label
        dtf['outcome'] = map(lambda x:1 if x else 0, y)
        group = dtf.groupby('topic').sum()
        group['total'] = dtf.groupby('topic').count()
        group['pct'] = group.outcome/group.total

        return group


    def describe_nmf_results(full_tf, H, W,y_train, n_top_words = 10):
        '''
        Retrieve top n words describing NMF latent topics, along with
        corresponding success rates.
        '''
        feature_words = full_tf.get_feature_names()
        top_topic_words = []
        for topic_num, topic in enumerate(H):
            top_words = [feature_words[i] for i in topic.argsort()[:-n_top_words - 1:-1]]
            top_topic_words.append([topic_num,top_words])


        nmf_df = pd.DataFrame(top_topic_words, columns=['topic','top_words'])
        group = get_success_pct_per_topic(W_train,y_train)

        mdf = group.merge(nmf_df, left_on='index1', right_on='topic',how='outer')
        return mdf
