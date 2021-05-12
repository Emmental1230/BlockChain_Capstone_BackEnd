from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from .models import Member
from .serializers import MemberSerializer
from subprocess import Popen, PIPE, STDOUT 
from django.http import HttpResponse
import subprocess, hashlib, json, os, random, base62
import asyncio
from asgiref.sync import async_to_sync
from asgiref.sync import sync_to_async

#import bcrypt
# Create your views here.

@csrf_exempt
def member_list(request):

    #해당 학생 data 반환
    if request.method == 'GET': 
        if not 'key' in request.GET :   #key가 없을 경우 error 출력
            return JsonResponse({'msg' : 'params error'}, status=400)

        hash_key = request.GET.get('key', None)

        try :
            obj = Member.objects.get(email_hash=hash_key)
            serializer = MemberSerializer(obj)
            return JsonResponse(serializer.data, status=201, safe=False)
        except :
            return JsonResponse({'msg' : 'Key is not exist'}, status=400)

    #회원가입 요청
    elif request.method == 'POST':
        if not 'key' in request.GET :   #key가 없을 경우 error 출력
            return JsonResponse({'msg' : 'params error'}, status=400)

        api_key = request.GET.get('key', None)
        if api_key != '6a7f2b72ec2befee1cdb125a9ce96e8bfcac2484ad7a068024fc1b946d38bffe' :  #이 주석 보면 저 해싱값이 뭘 뜻하는건지 써줘 기우
            return JsonResponse({'msg' : 'Key error'}, status=400)

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
        salt = bytes( base62.encodebytes(os.urandom(16)), encoding="utf-8")
        email_dump = json.dumps(email, sort_keys = True).encode() + salt
        email_hash = hashlib.sha256(email_dump).hexdigest()
        data['email_hash'] = email_hash
        
        serializer = MemberSerializer(data=data)

        #if pk == 'temporaryKey':         #app사용자인지 확인
        if serializer.is_valid():       #입력 data들 포맷 일치 여부 확인
            serializer.save()
            return JsonResponse({'email_hash': email_hash}, status=201)
        else:
            return JsonResponse({'msg' :'data format이 일치하지 않습니다.'}, status=400)


@csrf_exempt
@sync_to_async
@async_to_sync
async def run_python(request):
    if request.method == 'POST':
        email = request.GET.get('email', None)
        simple_pw = request.GET.get('SimplePassword', None)

        command = ["sh","/home/caps/indy/start_docker/api.sh","ed1ff7a2fc14 " + email + " " + simple_pw]
        # command = "sh /home/caps/indy/start_docker/api.sh ed1ff7a2fc14 " + email +" "+ simple_pw
        try:
            process = Popen(command, stdout=PIPE, stderr=STDOUT)
            process.wait()
            with open('/home/caps/indy/start_docker/data.json')as f:
                json_data = json.load(f)
                #email = json_data['email']
                did = json_data['did']

        except Exception as e:
            return JsonResponse({'msg':'failed_Exception','erreor 내용':str(e)}, status=400)
        return JsonResponse({'email':email,'simple_pw':simple_pw})
        #return JsonResponse(json_data, status=201)


@csrf_exempt
def findmyinfo(request):
    #email, stdnum 받을 경우, 해당 key값 반환
    if request.method == 'POST':

        if not 'key' in request.GET :   #key가 없을 경우 error 출력
            return JsonResponse({'msg' : 'params error'}, status=400)
        api_key = request.GET.get('key', None)
        if api_key != '6a7f2b72ec2befee1cdb125a9ce96e8bfcac2484ad7a068024fc1b946d38bffe' :  #이 주석 보면 저 해싱값이 뭘 뜻하는건지 써줘 기우
            return JsonResponse({'msg' : 'Key error'}, status=400)

        data = JSONParser().parse(request)
        studentDB = Member.objects.all()

        #email 정보가 DB에 있는지 확인
        if studentDB.filter(email = data['email']).exists() :
            std = Member.objects.get(email = data['email'])     #해당 학생 정보 저장

            #stdnum부분이 공란일 경우 or
            #stdnum가 있고 email, stdnum이 한사람의 정보일 경우
            if not data['stdnum']  or std.stdnum == data['stdnum'] :
                return JsonResponse({'email_hash': std.email_hash }, status=201)
            else :
                return JsonResponse({'msg':'email과 stdnum이 일치하지 않습니다.'}, status=400)
        else :
            return JsonResponse({'msg': '가입되지 않은 email입니다.'}, status=400)


'''
@csrf_exempt
def member(request, word):
    #학생 수정
    obj = Member.objects.get(email_hash=word)
    if request.method == 'GET':
        serializer = MemberSerializer(obj)
        return JsonResponse(serializer.data, status=201, safe=False)  
'''

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