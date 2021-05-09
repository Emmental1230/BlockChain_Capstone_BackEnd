from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from .models import Member
from .serializers import MemberSerializer
from subprocess import Popen, PIPE, STDOUT 
from django.http import HttpResponse
import subprocess
import hashlib
import json
import os
import random
import base62
#import bcrypt
# Create your views here.


@csrf_exempt
def member_list(request):
    #모든 학생들 조회
    if request.method == 'GET':
        members = Member.objects.all()
        serializer = MemberSerializer(members, many=True)
        return JsonResponse(serializer.data, safe=False, status=201)

    #회원가입 요청
    elif request.method == 'POST':
        data = JSONParser().parse(request)
        studentDB = Member.objects.all()

        email = data['email']
        stdnum = data['stdnum']

        #중복 회원여부 확인
        if studentDB.filter(email = email).exists() :
            return JsonResponse({'msg':'Email is already exists'}, status=400)
        elif studentDB.filter(stdnum = stdnum).exists() :
            return JsonResponse({'msg':'stdnum is already exists'}, status=400)
        
        #email 해시 하는 부분

        #ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        salt = base62.encodebytes(os.urandom(16))
        salt = bytes(salt, encoding="utf-8")
        #for i in range(16):
        #    salt.append(random.choice(ALPHABET))

        #salt_string = "".join(salt)

        email_dump = json.dumps(email, sort_keys = True).encode()
        email_dump += salt

        email_hash = hashlib.sha256(email_dump).hexdigest()
        email_data_json = { 'email_hash' : '' }
        email_data_json['email_hash'] = email_hash
        data['email_hash'] = email_hash

        serializer = MemberSerializer(data=data)

        #if pk == 'temporaryKey':         #app사용자인지 확인
        if serializer.is_valid():       #입력 data들 포맷 일치 여부 확인
            serializer.save()
            return JsonResponse(email_data_json, status=201)

        return JsonResponse(serializer.errors, status=400)       


@csrf_exempt
def member(request, word):
    #학생 수정
    obj = Member.objects.get(email_hash=word)

    if request.method == 'GET':
        serializer = MemberSerializer(obj)
        return JsonResponse(serializer.data, status=201, safe=False)
    
    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = MemberSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)   


@csrf_exempt
def run_python(request): 
    if request.method == 'GET': 
        command = ["sh","/home/caps/indy/start_docker/api.sh","f92f65a3731e","test@kyonggi.ac.kr"]
        try: 
            process = Popen(command, stdout=PIPE, stderr=STDOUT) 
#            output = process.stdout.read() 
#            exitstatus = process.poll() 
#            pwd = os.path.realpath(__file__)
            with open('/home/caps/indy/start_docker/data.json')as f:               
                json_data = json.load(f)
                email = json_data['email']
                did = json_data['did']
            
                #result = {"status": "Failed  ", "output":str(output)}


        except Exception as e: 
            #result =  {"status": "failed_Exception"  , "output":str(e)} 
            return JsonResponse({'msg':'failed_Exception','erreor 내용':str(e),'pwd':pwd}, status=400)

        return JsonResponse(json_data, status=201)

#현재 안씀
'''
@csrf_exempt
def readDID(request): 
    with open('../docker/Blockchain_Capstone_Indy/start_docker/data.json')as f:
        json_data = json.load(f)
        email = json_data['email']
        did = json_data['did']
    return JsonResponse(json_data, status=201)
'''

@csrf_exempt
def findmyinfo(request):
    #email, stdnum 받을 경우, 해당 key값 반환
    if request.method == 'POST':
        data = JSONParser().parse(request)
        studentDB = Member.objects.all()
        #email = "1544455cac2644c63b59551bc9e135a38cd9b59ba2ca4f475d45a41737bf3f62"
        #stdnum = "12341234"

        if studentDB.filter(email = data['email']).exists() :
            email = studentDB.filter(email = data['email'])
            stdnum = studentDB.filter(stdnum = data['stdnum'])
            if email[0]==stdnum[0] :
                #email 과 stdnum이 한 사람의 정보일 경우 진행
                #반환값을 만들고 해당 값을 반환하면됨
                return JsonResponse({'email':email_hash}, status=201)
            else :
                return JsonResponse({'msg':'email과 stdnum이 일치하지 않습니다.'}, status=400)
        else :
            return JsonResponse({'msg': '가입되지 않은 email입니다.'}, status=400)
