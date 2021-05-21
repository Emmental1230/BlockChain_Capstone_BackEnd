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
import time
from asgiref.sync import async_to_sync
from asgiref.sync import sync_to_async

# Create your views here.
containerId = "6db8a03cdd8d" #containerId 선언
tempkey = "이팔청춘의 U-PASS"    #tmpkey 선언
@csrf_exempt
# 임시키 확인
def check_tempkey(request, compare_key):
    if not 'key' in request.GET:
        return JsonResponse({'msg': 'parmas error'}, status=400)

    api_key = request.GET.get('key', None)

    if api_key != compare_key:
        return JsonResponse({'msg': 'Key is error'}, status=400)
            
# DB check
def checkDB(api_key):
    studentDB = Member.objects.all()
    if studentDB.filter(user_key=api_key).exists():
        return True
    else:
        return False

@csrf_exempt
def member_list(request):
    # 회원가입 요청
    if request.method == 'POST':
        check_tempkey(request, hashlib.sha256(tempkey.encode()))
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

@csrf_exempt
def password(request):
    #간편 비밀번호 저장
    if request.method == 'POST':
        if not 'key' in request.GET:
            return JsonResponse({'msg': 'params error'}, status=400)
        if not 'SimplePassword' in request.GET:
            return JsonResponse({'msg': 'params error'}, status=400)

        api_key = request.GET.get('key', None)  # key 추출
        wallet_key = request.GET.get('SimplePassword', None)  # 간편 pwd 추출
        
        if checkDB(api_key):
            student = Member.objects.get(user_key = api_key)
            student.wallet_key = wallet_key
            student.save()
            return JsonResponse({'msg':"save complete"},status=201)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)

    #간편 비밀번호 찾기
    elif request.method == 'GET':
        if not 'key' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)

        api_key = request.GET.get('key', None)  # key 추출
        if checkDB(api_key):
            student = Member.objects.get(user_key=api_key)  # 해당 학생 정보 저장
            wallet_key = student.wallet_key
            return JsonResponse({'wallet_key': wallet_key}, status=201)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)


@csrf_exempt
# did 발급
def generate_did(request):
    if request.method == 'POST':
        if not 'key' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)

        api_key = request.GET.get('key', None)  # key 추출
        student = Member.objects.get(user_key = api_key)
        email = student.email
        if checkDB(api_key):
            timestamp = time.time() #타임스탬프
            #info_hash = hashlib.sha256(info_dump.encode('utf-8')).hexdigest()
            wallet_name = hashlib.sha256((email + str(timestamp)).encode()).hexdigest() # wallet_name (이메일 + timestamp) 생성
            wallet_key = request.GET.get('SimplePassword', None)  # 간편 pwd 추출
            student_id = request.GET.get('studentId', None)  # 학번 params 가져오기
            command = ["sh","../indy/start_docker/sh_generate_did.sh", containerId, wallet_name, wallet_key, student_id] #did발급 명령어
            try:
                # 명령어 인자로 하여 Popen 실행
                process = Popen(command, stdout=PIPE, stderr=PIPE)
                process.wait()  # did 재발급까지 대기

                with open('/home/deploy/data.json')as f:  # server로 복사된 did 열기
                    json_data = json.load(f)  # json_data에 json으로 저장
                    error = json_data['error']
                    if error == 'Error':
                        return JsonResponse({'msg': 'DID 발급 오류'}, status=400)
                    
                    student.did = json_data['did']  #Did 저장
                    student.wallet_id = wallet_name # 새로운 wallet_name 저장
                    student.save()

                    os.remove("/home/deploy/data.json") #생성된 파일 삭제
                    
            except Exception as e:
                return JsonResponse({'msg': 'failed_Exception', 'error 내용': str(e)}, status=400)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)
        return JsonResponse({'did':student.did , 'error': error}, status=201)

@csrf_exempt
#did 재발급
def regenerate_did(request):
    if request.method == 'POST':
        if not 'key' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)

        api_key = request.GET.get('key', None)  # key 추출
        if checkDB(api_key):
            #DB에서 key 가지고 email, did 가져오기
            student = Member.objects.get(user_key=api_key)
            old_wallet_name = student.wallet_id
            did = student.did # did
            email = student.email # 이메일
            timestamp = time.time() #타임스탬프
            new_wallet_name = hashlib.sha256((email + str(timestamp)).encode()).hexdigest()  # wallet_name (이메일 + timestamp) 생성
            wallet_key = request.GET.get('SimplePassword', None)  # 간편 pwd 추출
            student_id = request.GET.get('studentId', None)  # 학번 params 가져오기

            #DB에 wallet_name 저장 필요
            command = ["sh","../indy/start_docker/sh_regenerate_did.sh", containerId, did, student_id, email, new_wallet_name, wallet_key ] #did 재발급 명령어
            try:
                # 명령어 인자로 하여 Popen 실행
                process = Popen(command, stdout=PIPE, stderr=PIPE)
                process.wait()  # did 발급까지 대기
                output = process.stdout.read()
                # return JsonResponse({'output': str(output)}, status=400)

                with open('/home/deploy/' + str(student_id) + 'NewWalletID.json') as f:  # server로 복사된 did 열기
                    json_data = json.load(f)  # json_data에 json으로 저장
                    # 에러 추가 
                    if json_data['error'] == 'Error':
                        return JsonResponse({'msg': 'DID 재발급 오류'}, status=400)
                    new_wallet_name=json_data['new_wallet']
                    student.wallet_id = new_wallet_name # 새로운 wallet_name 저장
                    student.save()
                    os.remove('/home/deploy/' + str(student_id) + 'NewWalletID.json') # 생성된 파일 삭제
            except Exception as e:
                return JsonResponse({'msg': 'failed_Exception', 'error 내용': str(e)}, status=400)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)
        return JsonResponse({'did':student.did , 'new_wallet_name': new_wallet_name, 'old_wallet_name':old_wallet_name }, status=201)

@csrf_exempt
# did 찾기
def get_did(request):
    if request.method == 'GET':
        if not 'key' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)
        api_key = request.GET.get('key', None)  # key 추출

        if checkDB(api_key):
            student = Member.objects.get(user_key=api_key)
            wallet_name = student.wallet_id  # wallet_name 디비에서 찾아오기
            wallet_key = request.GET.get('SimplePassword', None)  # 간편 pwd 추출
            command = ["sh", "../indy/start_docker/sh_get_did.sh",
                        containerId, wallet_name, wallet_key]  
            try:
                # 명령어 인자로 하여 Popen 실행
                process = Popen(command, stdout=PIPE, stderr=PIPE)
                output = process.stdout.read()
                process.wait()  # did 발급까지 대기
                with open('/home/deploy/student_did.json')as f:  # server로 복사된 did 열기(학생이름으로 필요)
                    json_data = json.load(f)  # json_data에 json으로 저장
                    if json_data['error'] == 'Error':
                        return JsonResponse({'msg': 'DID를 찾을 수 없습니다.'}, status=400)
                    os.remove("/home/deploy/student_did.json") #생성된 파일 삭제
            except Exception as e:
                return JsonResponse({'msg': 'failed_Exception', 'error 내용': str(e)}, status=400)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)
        return JsonResponse(json_data, status=201)


@csrf_exempt
# 회원찾기
def findmyinfo(request):
    if request.method == 'POST':
        check_tempkey(request, hashlib.sha256(tempkey.encode()))
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

@csrf_exempt
# 출입 여부 찾기
def get_entry(request):
    if request.method == 'GET':
        if not 'key' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)
        api_key = request.GET.get('key', None)  # key 추출

        if checkDB(api_key):
            student = Member.objects.get(user_key=api_key)
            wallet_name = student.wallet_id # wallet_name 생성
            wallet_key = request.GET.get('SimplePassword', None)  # 간편 pwd 추출
            did = request.GET.get('did', None)
            year = request.GET.get('year', None)
            month = request.GET.get('month', None)
            day = request.GET.get('day', None)

            command = ["sh", "../indy/start_docker/sh_get_attrib.sh",
                       containerId, wallet_name, wallet_key, did, year, month, day]
            try:
                # 명령어 인자로 하여 Popen 실행
                process = Popen(command, stdout=PIPE, stderr=PIPE)
                output = process.stdout.read()
                process.wait()  # did 발급까지 대기
                with open('/home/deploy/attrib.json')as f:  # server로 복사된 did 열기
                    json_data = json.load(f)  # json_data에 json으로 저장
                os.remove("/home/deploy/attrib.json") #생성된 파일 삭제
            except Exception as e:
                return JsonResponse({'msg': 'failed_Exception', 'error 내용': str(e)}, status=400)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)

        return JsonResponse(json_data, status=201)


@csrf_exempt
# 출입 등록
def generate_entry(request):
    if request.method == 'POST':
        if not 'key' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)
        api_key = request.GET.get('key', None)  # key 추출
        
        if checkDB(api_key):
            student = Member.objects.get(user_key=api_key)

            wallet_name = student.wallet_id # wallet_name 생성
            wallet_key = request.GET.get('SimplePassword', None)  # 간편 pwd 추출
            did = request.GET.get('did', None)
            year = request.GET.get('year', None)
            building = request.GET.get('building', None)
            month = request.GET.get('month', None)
            day = request.GET.get('day', None)
        
            command = ["sh", "../indy/start_docker/sh_generate_attrib.sh",
                       containerId, wallet_name, wallet_key, did, building, year, month, day]
            try:
                # 명령어 인자로 하여 Popen 실행
                process = Popen(command, stdout=PIPE, stderr=PIPE)
                output = process.stdout.read()
                process.wait()  # did 발급까지 대기
                return JsonResponse({'output': str(output)}, status=201)

                with open('/home/deploy/gen_attrib.json')as f:  # server로 복사된 did 열기
                    json_data = json.load(f)  # json_data에 json으로 저장
                # os.remove("/home/deploy/gen_attrib.json") #생성된 파일 삭제
            except Exception as e:
                return JsonResponse({'msg': 'failed_Exception', 'error 내용': str(e)}, status=400)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)

        # return JsonResponse(json_data, status=201)


'''
@csrf_exempt
def member(request, word):
    #학생 수정
    obj = Member.objects.get(email_hash=word)
    if request.method == 'GET':
        serializer = MemberSerializer(obj)
        return JsonResponse(serializer.data, status=201, safe=False)  
'''
