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
import asyncio
from asgiref.sync import async_to_sync
from asgiref.sync import sync_to_async

#import bcrypt
# Create your views here.


@csrf_exempt
# 임시키 확인
def check_tempkey(request, compare_key):
    if not 'key' in request.GET:
        return JsonResponse({'msg': 'parmas error'}, status=400)

    api_key = request.GET.get('key', None)

    if api_key != compare_key:
        return JsonResponse({'msg': 'Key is error'}, status=400)


@csrf_exempt
def member_list(request):
    # 회원가입 요청
    if request.method == 'POST':
        check_tempkey(request, hashlib.sha256('이팔청춘의 U-PASS'.encode()))
        stdnum = request.GET.get('stdnum', None)
        major = request.GET.get('major', None)
        name = request.GET.get('name', None)
        email = request.GET.get('email', None)

        studentDB = Member.objects.all()

        # 중복 회원여부 확인
        if studentDB.filter(email=email).exists():
            return JsonResponse({'msg': 'Email is already exists'}, status=400)

        # info_hash 해시 하는 부분
        info_dump = str(stdnum) + str(major) + str(name) + str(email)
        info_hash = hashlib.sha256(info_dump.encode('utf-8')).hexdigest()

        # user_key 해시 하는 부분
        salt = base62.encodebytes(os.urandom(16))
        salt = bytes(salt, encoding="utf-8")

        email_dump = info_dump + str(salt)
        user_key = hashlib.sha256(email_dump.encode('utf-8')).hexdigest()
        user_key_json = {'user_key': ''}
        user_key_json['user_key'] = user_key

        data = {'email': '', 'info_hash': '', 'user_key': ''}
        data['email'] = email
        data['info_hash'] = info_hash
        data['user_key'] = user_key

        serializer = MemberSerializer(data=data)

        if serializer.is_valid():  # 입력 data들 포맷 일치 여부 확인
            serializer.save()
            return JsonResponse(user_key_json, status=201)

        return JsonResponse(serializer.errors, status=400)

# DB check
def checkDB(api_key):
    studentDB = Member.objects.all()
    if studentDB.filter(user_key=api_key).exists():
        return True
    else:
        return False

@csrf_exempt
# did 발급
def generate_did(request):
    if request.method == 'POST':
        if not 'key' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)

        api_key = request.GET.get('key', None)  # key 추출

        if checkDB(api_key):
            wallet_id = api_key  # wallet_name 생성
            wallet_key = request.GET.get('SimplePassword', None)  # 간편 pwd 추출
            command = ["sh", "../indy/start_docker/sh_generate_did.sh",
                       "095b8a7a52ec", wallet_id, wallet_key]  # did발급 명령어
            try:
                # 명령어 인자로 하여 Popen 실행
                process = Popen(command, stdout=PIPE, stderr=PIPE)
                process.wait()  # did 발급까지 대기
                with open('/home/deploy/data.json')as f:  # server로 복사된 did 열기
                    json_data = json.load(f)  # json_data에 json으로 저장
                    os.remove("/home/deploy/data.json") #생성된 파일 삭제
            except Exception as e:
                return JsonResponse({'msg': 'failed_Exception', 'error 내용': str(e)}, status=400)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)
        return JsonResponse(json_data, status=201, safe=False)


@csrf_exempt
# did 찾기
def get_did(request):
    if request.method == 'GET':
        if not 'key' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)

        api_key = request.GET.get('key', None)  # key 추출

        if checkDB(api_key):
            wallet_id = api_key  # wallet_name 생성
            wallet_key = request.GET.get('SimplePassword', None)  # 간편 pwd 추출
            command = ["sh", "../indy/start_docker/sh_get_did.sh",
                       "095b8a7a52ec", wallet_id, wallet_key]  # did찾기 명령어 origin : 1b57c8002249    YG : f57bccba3b28  Kiwoo : 
            try:
                # 명령어 인자로 하여 Popen 실행
                process = Popen(command, stdout=PIPE, stderr=PIPE)
                output = process.stdout.read()
                process.wait()  # did 발급까지 대기
                with open('/home/deploy/student_did.json')as f:  # server로 복사된 did 열기(학생이름으로 필요)
                    json_data = json.load(f)  # json_data에 json으로 저장
                    if json_data['error'] == 'Error':
                        return JsonResponse({'msg': 'DID를 찾을 수 없습니다.'}, status=400)
                    os.remove("/home/deploy/data.json") #생성된 파일 삭제
            except Exception as e:
                return JsonResponse({'msg': 'failed_Exception', 'error 내용': str(e)}, status=400)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)
        # return JsonResponse({'output':str(output)}, status=201)
        return JsonResponse(json_data, status=201, safe=False)


@csrf_exempt
# 회원찾기
def findmyinfo(request):
    if request.method == 'POST':
        check_tempkey(r-equest, hashlib.sha256('이팔청춘의 U-PASS'.encode()))
        stdnum = request.GET.get('stdnum', None)
        major = request.GET.get('major', None)
        name = request.GET.get('name', None)
        email = request.GET.get('email', None)

        info_dump = str(stdnum) + str(major) + str(name) + str(email)
        info_hash = hashlib.sha256(info_dump.encode('utf-8')).hexdigest()
        studentDB = Member.objects.all()

        # email 정보가 DB에 있는지 확인
        if studentDB.filter(email=email).exists():
            # 제대로된 정보 입력했는지 확인
            if studentDB.filter(info_hash=info_hash).exists():
                std = Member.objects.get(info_hash=info_hash)  # 해당 학생 정보 저장
                return JsonResponse({'user_key': std.user_key}, status=201)
            else:
                return JsonResponse({'msg': '잘못된 정보를 입력하였습니다.'}, status=400)
        else:
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