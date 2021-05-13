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
#임시키 확인
def check_tempkey(request, compare_key):
    if not 'key' in request.GET :
        return JsonResponse({'msg' : 'parmas error'}, status=400)

    api_key = request.GET.get('key', None)
    
    if api_key != compare_key:
        return JsonResponse({'msg' : 'Key is error'}, status=400)

@csrf_exempt
def member_list(request):
    #회원가입 요청
    if request.method == 'POST':
        check_tempkey(request, hashlib.sha256('이팔청춘의 U-PASS'.encode()))
        stdnum = request.GET.get('stdnum', None)
        major = request.GET.get('major', None)
        name = request.GET.get('name', None)
        email = request.GET.get('email', None)

        studentDB = Member.objects.all()

        #중복 회원여부 확인
        if studentDB.filter(email = email).exists() :
            return JsonResponse({'msg':'Email is already exists'}, status=400)

        #info_hash 해시 하는 부분
        info_dump = str(stdnum) + str(major) + str(name) + str(email)
        info_hash = hashlib.sha256(info_dump.encode('utf-8')).hexdigest()


        #user_key 해시 하는 부분
        salt = base62.encodebytes(os.urandom(16))
        salt = bytes(salt, encoding="utf-8")

        email_dump = info_dump + str(salt)
        user_key = hashlib.sha256(email_dump.encode('utf-8')).hexdigest()
        user_key_json = { 'user_key' : '' }
        user_key_json['user_key'] = user_key

        data = { 'email' : '', 'info_hash' : '', 'user_key' : '' }
        data['email'] = email
        data['info_hash'] = info_hash
        data['user_key'] = user_key

        serializer = MemberSerializer(data=data)

        if serializer.is_valid():       #입력 data들 포맷 일치 여부 확인
            serializer.save()
            return JsonResponse(user_key_json, status=201)

        return JsonResponse(serializer.errors, status=400)

@csrf_exempt
@sync_to_async
@async_to_sync
def did_shell(command):
    process = Popen(command, stdout=PIPE, stderr=PIPE)  #명령어 인자로 하여 Popen 실행  
    #process.wait()  #did 발급까지 대기
    with open('/home/deploy/data.json')as f:    #server로 복사된 did 열기
        json_data = json.load(f)   #json_data에 json으로 저장
    print(json_data)
    return json_data
    

@csrf_exempt
def run_python(request):
    if request.method == 'POST':
        if not 'key' in request.GET :
            return JsonResponse({'msg' : 'parmas error'}, status=400)

        studentDB = Member.objects.all()
        api_key = request.GET.get('key', None)  #key 추출

        if studentDB.filter(user_key = api_key).exists() :
            wallet_name = api_key #wallet_name 생성
            wallet_key = request.GET.get('SimplePassword', None) #간편 pwd 추출
            command = ["sh","../indy/start_docker/api.sh","1b57c8002249", wallet_name, wallet_key] #did발급 명령어
            try:
                result = did_shell(command)
            except Exception as e:
                return JsonResponse({'msg':'failed_Exception','error 내용':str(e)}, status=400)
        else :
            return JsonResponse({'msg' : 'Key is error'}, status=400)
        
        return JsonResponse(result, status=201, safe=False)


@csrf_exempt
def findmyinfo(request):
    #email, stdnum 받을 경우, 해당 key값 반환
    if request.method == 'POST':

        # if not 'key' in request.GET :   #key가 없을 경우 error 출력
        #     return JsonResponse({'msg' : 'params error'}, status=400)
        # api_key = request.GET.get('key', None)
        # if api_key != '6a7f2b72ec2befee1cdb125a9ce96e8bfcac2484ad7a068024fc1b946d38bffe' :  #이 주석 보면 저 해싱값이 뭘 뜻하는건지 써줘 기우
        #     return JsonResponse({'msg' : 'Key error'}, status=400)
        check_tempkey(request, hashlib.sha256('이팔청춘의 U-PASS'.encode()))
        email = request.GET.get('email', None)

        studentDB = Member.objects.all()

        #email 정보가 DB에 있는지 확인
        if studentDB.filter(email = email).exists() :
            std = Member.objects.get(email = email)     #해당 학생 정보 저장
            return JsonResponse({'user_key': std.user_key }, status=201)
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
