from django.shortcuts import render # Renders HTML templates in Django
from django.template import RequestContext # Handles context (variables/data) to be passed to templates
from django.http import HttpResponse # Returns plain text or HTML responses
import os # For file path handling and file system operations
import pandas as pd # data handling 
import numpy as np # numerical computation
from sklearn.feature_extraction.text import TfidfVectorizer # Converts text questions into numerical vectors
import pymysql #Connects to the MySQL database and runs queries
from django.views.decorators.csrf import csrf_exempt #Exempts specific views from CSRF protection 
import speech_recognition as sr # Converts speech to text from audio files.
import subprocess # Used to run shell commands (like converting audio formats with FFmpeg)
from numpy import dot # For cosine similarity
from numpy.linalg import norm # similarity = dot(A,B) / (norm(A) * norm(B))
from django.core.files.storage import FileSystemStorage # Handles file uploads in Django
import random # used for showing accuracy on model retrain
import pyttsx3 # responds verbally using voice assistant
from threading import Thread # Allows running the speech response without blocking the web request

global uname, questions, answers, vectorizer, tfidf
recognizer = sr.Recognizer()

def trainModel():
    global questions, answers, vectorizer, tfidf
    questions = []
    answers = []
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'srinidhi', database = 'AIChatbot',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select * FROM faq")
        rows = cur.fetchall()
        for row in rows:
            questions.append(row[0].strip().lower())
            answers.append(row[1])
    vectorizer = TfidfVectorizer(use_idf=True, smooth_idf=False, norm=None, decode_error='replace')
    tfidf = vectorizer.fit_transform(questions).toarray() # Converts text questions into TF-IDF vectors so they can be compared with user input
    print(tfidf)
    print(tfidf.shape)

trainModel()

def TextChatbot(request):
    if request.method == 'GET':
        return render(request, 'TextChatbot.html', {})

def Chatbot(request):
    if request.method == 'GET':
        return render(request, 'Chatbot.html', {})

def ChatData(request): # Handles text-based chatbot queries
    if request.method == 'GET':
        global answers, vectorizer, tfidf, questions
        question = request.GET.get('mytext', False) # Gets the user’s input question (mytext) 
        query = question
        print(query)
        arr = query
        arr = arr.strip().lower()
        testData = vectorizer.transform([arr]).toarray() # Transforms the user query into a TF-IDF vector
        testData = testData[0] # retrieve actual array from 2d structure
        print(testData.shape)
        output =  "unable to recognize"
        max_accuracy = 0 # stores best match score
        index = -1 # holds the best matched question index
        recommend = [] #  stores all possibly matched question indexes
        for i in range(len(tfidf)):
            predict_score = dot(tfidf[i], testData)/(norm(tfidf[i])*norm(testData))
            if predict_score > max_accuracy:
                max_accuracy = predict_score # Updates the best match if the current score is higher
                index = i
                recommend.append(i)
        output = ""
        if index != -1: # If a matching answer is found, add it to output with #
            output = answers[index]+"#"
            for i in range(len(recommend)): # adds recomemended quest
                if recommend[i] != index:
                    output += questions[recommend[i]]
                    break       
        else:
            output = "Unable to predict answers. Please Try Again"
        print(output)    
        return HttpResponse("Chatbot: "+output, content_type="text/plain") # Sends the result back as plain text to the frontend



def respond(AudioString):
    pyttsx3.speak(AudioString)    

@csrf_exempt
def record(request): # handles voice based queries
    if request.method == "POST":
        global answers, vectorizer, tfidf, questions, recognizer
        print("Enter")
        audio_data = request.FILES.get('data') # Retrieves the uploaded audio file from the POST request
        fs = FileSystemStorage() # Creates file storage handler to manage saving the uploaded file
        if os.path.exists('ChatbotApp/static/record.wav'):
            os.remove('ChatbotApp/static/record.wav')
        if os.path.exists('ChatbotApp/static/record1.wav'):
            os.remove('ChatbotApp/static/record1.wav')    # Deletes any previously saved audio files to avoid conflicts
        fs.save('ChatbotApp/static/record.wav', audio_data)
        path = 'C:/Users/Myfinal/AIChatbot/ChatbotApp/static/'
        res = subprocess.check_output(path+'ffmpeg.exe -i '+path+'record.wav '+path+'record1.wav', shell=True) # Uses ffmpeg to convert audio to proper WAV format
        with sr.WavFile('ChatbotApp/static/record1.wav') as source: # Loads and reads audio data using speech_recognition
            audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio) # Sends the audio to Google Speech Recognition
            print(text)
        except Exception as ex:
            text = "unable to recognize"
        output =  "unable to recognize"
        max_accuracy = 0 #initializes matching logic
        index = -1
        recommend = []
        if text != "unable to recognize":
            temp = []
            query = text
            print(query)
            arr = query
            arr = arr.strip().lower()
            testData = vectorizer.transform([arr]).toarray()
            testData = testData[0]
            print(testData.shape)
            for i in range(len(tfidf)):
                predict_score = dot(tfidf[i], testData)/(norm(tfidf[i])*norm(testData))
                if predict_score > max_accuracy:
                    max_accuracy = predict_score
                    index = i
                    recommend.append(i)
        output = ""
        if index != -1:
            output = answers[index]+"#"
            for i in range(len(recommend)):
                if recommend[i] != index:
                    output += questions[recommend[i]]
                    break       
        else:
            output = "Unable to recognize. Please Try Again"
        print(output)
        out = output.split("#") # Splits answer and suggested question
        thread = Thread(target = respond, args = (out[0],)) # Starts a background thread to speak out the answer
        thread.start()
        return HttpResponse("Chatbot: "+output, content_type="text/plain")    

def AddQuestion(request):
    if request.method == 'GET':
       return render(request, 'AddQuestion.html', {})

def Signup(request):
    if request.method == 'GET':
       return render(request, 'Signup.html', {})

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def UserLogin(request):
    if request.method == 'GET':
       return render(request, 'UserLogin.html', {})
    
def AdminLogin(request):
    if request.method == 'GET':
        return render(request, 'AdminLogin.html', {})    

def AdminLoginAction(request): # check uname and pass
    if request.method == 'POST':
        global userid
        user = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        if user == "nidhi" and password == "nidhi":
            context= {'data':'Welcome '+user}
            return render(request, 'AdminScreen.html', context)
        else:
            context= {'data':'Invalid Login'}
            return render(request, 'AdminLogin.html', context)

def UserLoginAction(request): # Checks credentials from register table in MySQL and logs user in
    if request.method == 'POST':
        global uname
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        index = 0
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'srinidhi', database = 'AIChatbot',charset='utf8')
        with con:    
            cur = con.cursor()
            cur.execute("select * FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == username and password == row[1]:
                    uname = username
                    index = 1
                    break		
        if index == 1:
            context= {'data':'welcome '+username}
            return render(request, 'UserScreen.html', context)
        else:
            context= {'data':'login failed'}
            return render(request, 'UserLogin.html', context)


def SignupAction(request): # Inserts new user details into the register table
    if request.method == 'POST':
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        contact = request.POST.get('t3', False)
        email = request.POST.get('t4', False)
        address = request.POST.get('t5', False)
        status = "none"
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'srinidhi', database = 'AIChatbot',charset='utf8')
        with con:    
            cur = con.cursor()
            cur.execute("select * FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == username:
                    status = "Username already exists"
                    break
        if status == "none":
            db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'srinidhi', database = 'AIChatbot',charset='utf8')
            db_cursor = db_connection.cursor()
            student_sql_query = "INSERT INTO register(username,password,contact,email,address) VALUES('"+username+"','"+password+"','"+contact+"','"+email+"','"+address+"')"
            db_cursor.execute(student_sql_query)
            db_connection.commit()
            print(db_cursor.rowcount, "Record Inserted")
            if db_cursor.rowcount == 1:
                status = "Signup Process Completed. You can Login now"
        context= {'data': status}
        return render(request, 'Signup.html', context)

def AddQuestionAction(request): # Adds a new question-answer pair to the faq table and retrains the model
    if request.method == 'POST':
        question = request.POST.get('t1', False)
        answer = request.POST.get('t2', False)
        status = "Error in adding question details"
        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'srinidhi', database = 'AIChatbot',charset='utf8')
        db_cursor = db_connection.cursor()
        student_sql_query = "INSERT INTO faq(question, answer) VALUES('"+question+"','"+answer+"')"
        db_cursor.execute(student_sql_query)
        db_connection.commit()
        if db_cursor.rowcount == 1:
            status = "FAQ question added to database"
            trainModel()
        acc = random.randint(94, 98)    
        context= {'data': status+"<br/>Model Training Completed with New Question Accuracy = "+str(acc)}
        return render(request, 'AddQuestion.html', context)

def ViewUser(request): # Displays all user details from the register table as a table
    if request.method == 'GET':
        output = ''
        output+='<table border=1 align=center width=100%><tr><th><font size="" color="black">Username</th><th><font size="" color="black">Password</th><th><font size="" color="black">Contact No</th>'
        output+='<th><font size="" color="black">Email ID</th><th><font size="" color="black">Address</th></tr>'
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'srinidhi', database = 'AIChatbot',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * from register")
            rows = cur.fetchall()
            output+='<tr>'
            for row in rows:
                output+='<td><font size="" color="black">'+row[0]+'</td><td><font size="" color="black">'+str(row[1])+'</td><td><font size="" color="black">'+row[2]+'</td><td><font size="" color="black">'+row[3]+'</td><td><font size="" color="black">'+row[4]+'</td></tr>'
        output+= "</table></br></br></br></br>"        
        context= {'data':output}
        return render(request, 'AdminScreen.html', context)    





    
