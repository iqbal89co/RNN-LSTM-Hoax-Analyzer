# Import Pandas
import pandas as pd
# Settingan di Pandas untuk menghilangkan warning
pd.options.mode.chained_assignment = None  # default='warn'

# Import Numpy
import numpy as np

# Loading Bar TQDM
from tqdm import tqdm

# Stopword Removal
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
from nltk.tokenize import word_tokenize

# Stemming (Sastrawi)
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# Tokenizer
from keras.preprocessing.text import Tokenizer
from keras.utils import pad_sequences

# Pickle FastText
import pickle

# Split Data
from sklearn.model_selection import train_test_split

# Model Building
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers import Embedding, Conv1D, GlobalMaxPooling1D, Dropout, LSTM, Dense
from tensorflow.keras.backend import clear_session
from keras.models import load_model

# Callbacks
from keras.callbacks import ModelCheckpoint
from tensorflow.keras.callbacks import EarlyStopping

# confusion matrix
from sklearn.metrics import confusion_matrix, accuracy_score

# Grafik
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style("whitegrid")
np.random.seed(0)

testSize = 0.15 #Pembagian ukuran datatesing

MAX_NB_WORDS = 100000 #Maximum jumlah kata pada vocabulary yang akan dibuat
max_seq_len = 100 #Panjang kalimatAmaximum

num_epochs = 40 #Jumlah perulangan / epoch saat proses training

aspek_kategori = ['label', 'judul', 'narasi']

def read_data(filename):
    # Membaca file CSV ke dalam Dataframe
    df = pd.read_csv(filename) 
    
    # Membagi dataframe menjadi data training & testing
    df_training, df_testing = train_test_split(df, test_size=testSize, random_state=42, shuffle=True)

    # Reset Index
    df_training = df_training.reset_index()
    df_testing = df_testing.reset_index()

    return df_training, df_testing

def preprocessing(data):
    # Case Folding
    data['lower'] = data['narasi'].str.lower()
    
    # Punctual Removal
    data['punctual'] = data['lower'].str.replace('[^a-zA-Z]+',' ', regex=True)
    
    # Normalization
    kamus_baku = pd.read_csv('kata_baku.csv', sep=";")
    dict_kamus_baku = kamus_baku[['slang','baku']].to_dict('list')
    dict_kamus_baku = dict(zip(dict_kamus_baku['slang'], dict_kamus_baku['baku']))
    norm = []
    for i in data['punctual']:
        res = " ".join(dict_kamus_baku.get(x, x) for x in str(i).split())
        norm.append(str(res))
    data['normalize'] = norm
    
    # Stopword Removal
    # stop_words = set(stopwords.words('indonesian'))
    # swr = []
    # for i in tqdm(data['normalize']):
    #     tokens = word_tokenize(i)
    #     filtered = [word for word in tokens if word not in stop_words]
    #     swr.append(" ".join(filtered))
    data['stopwords'] = data['normalize']
    
    # Stemming
    # factory = StemmerFactory()
    # stemmer = factory.create_stemmer()
    # stem = []
    # for i in tqdm(data['stopwords']):
    #     stem.append(stemmer.stem(str(i)))
    data['stemmed'] = data['normalize']
    
    return data

# Tokenisasi Training
def tokenize_training(data_training):
    global tokenizer #Menggunakan variabel global agar 'tokenizer' bisa dipake di luar fungsi ini
    tokenizer = Tokenizer(num_words = MAX_NB_WORDS, char_level=False)
    tokenizer.fit_on_texts(data_training['stemmed'])
    word_index = tokenizer.word_index
    
    train_sequences = tokenizer.texts_to_sequences(data_training['stemmed'])
    word_seq_train = pad_sequences(train_sequences, maxlen = max_seq_len)

    return word_index, word_seq_train


# Tokenisasi Testing
def tokenize_testing(data_testing):
    global tokenizer #Menggunakan variabel global agar 'tokenizer' bisa dipake di luar fungsi ini
    tokenizer = Tokenizer(num_words = MAX_NB_WORDS, char_level=False)
    test_sequences = tokenizer.texts_to_sequences(data_testing['stemmed'])
    word_seq_test = pad_sequences(test_sequences, maxlen = max_seq_len)

    return word_seq_test

# Tokenisasi secara umum
def tokenize(data):
    global tokenizer #Menggunakan variabel global agar 'tokenizer' bisa dipake di luar fungsi ini
    tokenizer = Tokenizer(num_words = MAX_NB_WORDS, char_level=False)
    sequences = tokenizer.texts_to_sequences(data['stemmed'])
    word_seq = pad_sequences(sequences, maxlen = max_seq_len)

    return word_seq

# Pendefenisian fungsi word embedding

def word_embedding(word_index):
    fasttext_word_to_index = pickle.load(open("fasttext_voc", 'rb'))
    
    words_not_found = []
    global nb_words
    nb_words = min(MAX_NB_WORDS, len(word_index)+1)

    global embed_dim
    embed_dim = 300 # dimensi matrix (dari fastTextnya cc.id.300.vec)
    global embedding_matrix
    embedding_matrix = np.zeros((nb_words, embed_dim))

    for word, index in word_index.items():
        if index < nb_words:
            embedding_vector = fasttext_word_to_index.get(word)
            if (embedding_vector is not None) and len(embedding_vector) > 0:
                embedding_matrix[index] = embedding_vector
            else:
                words_not_found.append(word)
    
    return embedding_matrix, nb_words, embed_dim

def model_building(x, y, x_val, y_val):
    model = keras.Sequential([
        keras.layers.Embedding(nb_words, embed_dim ,input_length=max_seq_len, 
                               weights=[embedding_matrix], trainable=False),
        keras.layers.LSTM(32),
        keras.layers.Dense(1, activation = 'sigmoid') #softmax
    ])
    model.summary()

    model.compile(
        optimizer = 'adam',
        loss = 'binary_crossentropy',
        metrics = ['accuracy']
    )

    es = tf.keras.callbacks.EarlyStopping(monitor='val_loss', mode='auto', patience=3)

    history = model.fit(x, y,
                        epochs = num_epochs, 
                        callbacks = [es],
                        validation_data=(x_val, y_val),
                        verbose = True # Verbose = 0 (tidak nampak progress), 1/True (progress bar), 2 (angka)
    )

    # plot learning curves
    plt.figure()
    plt.plot(history.history['loss'], lw=2.0, color='b', label='train')
    plt.plot(history.history['val_loss'], lw=2.0, color='r', label='val')
    plt.title("Loss History")
    plt.xlabel('Epochs')
    plt.ylabel('Cross-Entropy Loss')
    plt.legend(loc='upper right')
    plt.savefig("static/hasil/loss.png")

    plt.figure()
    plt.plot(history.history['accuracy'], lw=2.0, color='b', label='train')
    plt.plot(history.history['val_accuracy'], lw=2.0, color='r', label='val')
    plt.title("Accuracy History")
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend(loc='upper left')
    plt.savefig("static/hasil/accuracy.png")

    model.save("model/model_rnnlstm")

    loss_and_acc_train = model.evaluate(x, y, verbose=2)
    loss_train = round(loss_and_acc_train[0], 2)
    accuracy_train = round(loss_and_acc_train[1], 2)

    loss_and_acc_val = model.evaluate(x_val, y_val, verbose=2)
    loss_val = round(loss_and_acc_val[0], 2)
    accuracy_val = round(loss_and_acc_val[1], 2)

    clear_session()

    return loss_train, accuracy_train, loss_val, accuracy_val

def model_testing(file_test):
    df = pd.read_csv(file_test)

    # preprocessing
    df_testing = preprocessing(df)

    # tokenisasi
    word_seq_test = tokenize_testing(df_testing)

    # mendefinisikan dataframe hasil
    df_hasil = df_testing[['narasi', 'label']]

    # pemanggilan model
    model = load_model("model/model_rnnlstm")
    # proses presdiksi/testing
    pred = model.predict(word_seq_test)
    df_hasil['label_pred'] = (pred > 0.5).astype('int32')

    # confusion matrix
    cm = confusion_matrix(
        y_true=df_hasil['label'], y_pred=df_hasil['label_pred'])

    plt.figure(figsize=(8, 6))
    ax = plt.subplot()
    sns.heatmap(cm, annot=True, fmt='g')
    # annot=True untuk memberikan anotasi/tulisan pada setiap kotak
    # fmt='g' untuk menghilangkan notasi baku

    ax.set_xlabel('Predicted labels')
    ax.set_ylabel('True labels')
    ax.set_title('Confusion Matrix')
    ax.xaxis.set_ticklabels(['bukan_hoax', 'hoax'])
    ax.yaxis.set_ticklabels(['bukan_hoax', 'hoax'])

    plt.savefig("static/hasil/cm.png")
    
    # Akurasi
    accuracy = accuracy_score(df_hasil['label'], df_hasil['label_pred'])

    return df_hasil, accuracy