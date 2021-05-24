from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from .models import Member
from .models import Entry
from .serializers import MemberSerializer
from .serializers import EntrySerializer
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
from django.core.paginator import Paginator
from asgiref.sync import async_to_sync
from asgiref.sync import sync_to_async

containerId = "de0aedfd8579" #containerId 선언
tempkey = "이팔청춘의 U-PASS"    #tmpkey 선언
@csrf_exempt
# 임시키 검증
def check_tempkey(request, compare_key):
    if not 'key' in request.GET:
        return JsonResponse({'msg': 'parmas error'}, status=400)

    api_key = request.GET.get('key', None)

    if api_key != compare_key:
        return JsonResponse({'msg': 'Key is error'}, status=400)
            
# Key가 DB에 존재하는지 확인
def checkDB(api_key):
    studentDB = Member.objects.all()
    if studentDB.filter(user_key=api_key).exists():
        return True
    else:
        return False

# DID 검증
def check_did(did, timestamp, hashedData):
    #hashedData : qr에 담겨진 H(H(did + 간편비번))

    student = Member.objects.get(did = did)
    cmp1 = str(student.did_time_hash) + str(timestamp)
    cmp1_hash = hashlib.sha256(cmp1.encode('utf-8')).hexdigest()

    if hashedData == cmp1_hash:
        return True
    else:
        return False

# TimeStamp 검증( 오차허용범위  ±15sec )
def check_timestamp(qr):
    api_timestamp = time.time()
    api = int(api_timestamp)
    if abs(api - int(qr)) <= 15:
        return True
    else:
        return False

# 올바른 키인지 체크
@csrf_exempt
def auth_key(request):
    if request.method == 'GET':
        key = request.GET.get('key', None)
        studentDB = Member.objects.all()
        if studentDB.filter(user_key=key).exists():
            return JsonResponse({'msg': 'This is the correct key'}, status=201)
        else:
            return JsonResponse({'msg': 'Invalid key'}, status=400)

# 회원 키 GET 및 회원 가입 POST
@csrf_exempt
def member_list(request):
    # 키 발급
    if request.method == 'GET':
        studentDB = Member.objects.all()
        stdnum = request.GET.get('stdnum', None)
        major = request.GET.get('major', None)
        name = request.GET.get('name', None)
        email = request.GET.get('email', None)
        
        if studentDB.filter(email=email).exists():  # params로 전달받은 이메일이 DB에 존재하는지 확인
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

        return JsonResponse(user_key_json, status=201)
        
        
    # 회원가입  요청 +  did 발급
    if request.method == 'POST':
        check_tempkey(request, hashlib.sha256(tempkey.encode()))
        email = request.GET.get('email', None)
        studentDB = Member.objects.all()

        # 중복 회원여부 확인
        if studentDB.filter(email=email).exists():
            return JsonResponse({'msg': 'Email is already exists'}, status=400)
        
        user_key = request.GET.get('key', None)  # key 추출
        stdnum = request.GET.get('stdnum', None)
        major = request.GET.get('major', None)
        name = request.GET.get('name', None)
        info_dump = str(stdnum) + str(major) + str(name) + str(email)
        info_hash = hashlib.sha256(info_dump.encode('utf-8')).hexdigest()
        timestamp = int(time.time()) #타임스탬프
        wallet_name = hashlib.sha256((email + str(timestamp)).encode()).hexdigest() # wallet_name (이메일 + timestamp) 생성
        wallet_key = request.GET.get('SimplePassword', None)  # 간편 pwd 추출
        student_id = request.GET.get('studentId', None)  # 학번 params 가져오기
        command = ["sh","../indy/start_docker/sh_generate_did.sh", containerId, wallet_name, wallet_key, student_id] #did발급 명령어
        try:
            # 명령어 인자로 하여 Popen 실행
            process = Popen(command, stdout=PIPE, stderr=PIPE)
            process.wait()  # did 재발급까지 대기

            with open('../../deploy/data.json')as f:  # server로 복사된 did 열기
                json_data = json.load(f)  # json_data에 json으로 저장
                error = json_data['error']
                if error == 'Error':
                    return JsonResponse({'msg': 'DID 발급 오류'}, status=400)
                os.remove("/home/deploy/data.json") #생성된 파일 삭제
                did = json_data['did']  #Did 저장
                cmp1 = str(did) + str(wallet_key)
                did_time_hash = hashlib.sha256(cmp1.encode('utf-8')).hexdigest()
                    
                data = {'email': '', 'info_hash': '', 'user_key': '', 'wallet_id':'',  'did':'', 'did_time_hash':''}
                data['email'] = email
                data['info_hash'] = info_hash
                data['user_key'] = user_key
                data['wallet_id'] = wallet_name
                data['did'] = did
                data['did_time_hash'] = did_time_hash

                serializer = MemberSerializer(data=data)

                if serializer.is_valid():  # 입력 data들 포맷 일치 여부 확인    
                    serializer.save()
                    return JsonResponse({'did': did , 'error': error}, status=201)
                    
        except Exception as e:
            return JsonResponse({'msg': 'failed_Exception', 'error 내용': str(e)}, status=400)
        

# 간편 비밀번호 저장(POST) 및 찾기(GET)
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
        
        # DB에 해당 키가 존재한다면, 해당 튜플에 간편비밀번호 저장
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
        if checkDB(api_key):   # 해당 키가 DB에 존재 한다면,
            student = Member.objects.get(user_key=api_key)  # 해당 학생 정보 저장
            wallet_key = student.wallet_key
            if wallet_key is None:    # wallet_key 값이 DB에 저장되어 있지 않을때
                return JsonResponse({'msg': 'wallet_key is empty'}, status=400)

            return JsonResponse({'wallet_key': wallet_key}, status=201)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)

# DID 재발급
@csrf_exempt
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
            timestamp = int(time.time()) #타임스탬프
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

                with open('/home/deploy/' + str(student_id) + 'NewWalletID.json') as f:  # server로 복사된 did 열기
                    json_data = json.load(f)  # json_data에 json으로 저장
                    # 에러 추가 
                    if json_data['error'] == 'Error':
                        return JsonResponse({'msg': 'DID 재발급 오류'}, status=400)
                    new_wallet_name=json_data['new_wallet']
                    student.wallet_id = new_wallet_name # 새로운 wallet_name 저장
                    cmp1 = str(student.did) + str(wallet_key)
                    student.did_time_hash = hashlib.sha256(cmp1.encode('utf-8')).hexdigest()
                    student.save()
                    os.remove('/home/deploy/' + str(student_id) + 'NewWalletID.json') # 생성된 파일 삭제
            except Exception as e:
                return JsonResponse({'msg': 'failed_Exception', 'error 내용': str(e)}, status=400)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)
        return JsonResponse({'did':student.did , 'new_wallet_name': new_wallet_name, 'old_wallet_name':old_wallet_name }, status=201)

# DID 찾기
@csrf_exempt
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
                process.wait()  # did 발급까지 대기
                with open('/home/deploy/student_did.json')as f:  # server로 복사된 did 열기(학생이름으로 필요)
                    json_data = json.load(f)  # json_data에 json으로 저장
                    if json_data['error'] == 'Error':
                        return JsonResponse({'msg': 'DID를 찾을 수 없습니다.'}, status=400)
            except Exception as e:
                return JsonResponse({'msg': 'failed_Exception', 'error 내용': str(e)}, status=400)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)
        return JsonResponse(json_data, status=201)


#회원 찾기
@csrf_exempt
def findmyinfo(request):
    if request.method == 'GET':
        check_tempkey(request, hashlib.sha256(tempkey.encode()))
        stdnum = request.GET.get('stdnum', None)
        major = request.GET.get('major', None)
        name = request.GET.get('name', None)
        email = request.GET.get('email', None)

        info_dump = str(stdnum) + str(major) + str(name) + str(email) #전달 받은 학번,전공,이름,이메일 concat
        info_hash = hashlib.sha256(info_dump.encode('utf-8')).hexdigest() #해쉬
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


#출입 여부 찾기(Block Chain 상의 tx)
@csrf_exempt
def get_entry(request):
    if request.method == 'GET':
        if not 'key' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)
        api_key = request.GET.get('key', None)  # key 추출

        if checkDB(api_key):
            did = request.GET.get('did', None) # user did
            year = request.GET.get('year', None) # 연도
            month = request.GET.get('month', None) # 월

            command = ["sh", "../indy/start_docker/sh_get_attrib.sh",
                       containerId, did, year, month]
            try:
                # 명령어 인자로 하여 Popen 실행
                process = Popen(command, stdout=PIPE, stderr=PIPE)
                process.wait()  # did 발급까지 대기

                with open('/home/deploy/attrib.json')as f:  # server로 복사된 did 열기
                    json_data = json.load(f)  # json_data에 json으로 저장
                    os.remove("/home/deploy/attrib.json") #생성된 파일 삭제
                    if json_data['error'] == 'Error':
                        return JsonResponse({'msg': '출입한 내역이 없습니다.'}, status=400)
            except Exception as e:
                return JsonResponse({'msg': 'failed_Exception', 'error 내용': str(e)}, status=400)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)

        return JsonResponse(json_data, status=201)


# 출입 여부 등록
@csrf_exempt
def generate_entry(request):
    if request.method == 'POST':
        if not 'key' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)
        api_key = request.GET.get('key', None)  # key 추출
        
        if checkDB(api_key):
            student = Member.objects.get(user_key=api_key)

            wallet_name = student.wallet_id # wallet_name 생성
            wallet_key = request.GET.get('SimplePassword', None)  # 간편 pwd 추출
            admin_did =request.GET.get('admin_did', None)  # 간편 pwd 추출
            std_did = request.GET.get('std_did', None) # user did
            building = request.GET.get('building', None) # 출입 건물
            year = request.GET.get('year', None) # 연도
            month = request.GET.get('month', None) # 월
            day = request.GET.get('day', None) # 일
            timestamp = request.GET.get('timestamp', None) # timestamp
            hashedData = request.GET.get('hashedData', None) # hashedData

            if check_timestamp(timestamp):  #timestamp 유효범위 검증
                if check_did(std_did, timestamp, hashedData):   #qr 정보 검증
                    command = ["sh", "../indy/start_docker/sh_generate_attrib.sh",
                       containerId, wallet_name, wallet_key, admin_did, std_did, building, year, month, day]
                    try:
                        # 명령어 인자로 하여 Popen 실행
                        process = Popen(command, stdout=PIPE, stderr=PIPE)
                        process.wait()  # did 발급까지 대기
                        output = process.stdout.read()

                        with open('/home/deploy/gen_attrib.json')as f:  # server로 복사된 did 열기
                            json_data = json.load(f)  # json_data에 json으로 저장

                            if json_data['error'] == 'Error':
                                return JsonResponse({'msg': 'error'}, status=400)

                            entry_date = json_data['entry_date']
                            building_num = json_data['building_num']
                            entry_did = json_data['entry_did']
                            entry_time = json_data['entry_time']

                            data = {'entry_date': '', 'building_num': '', 'entry_did': '', 'entry_time' : ''}
                            data['entry_date'] = entry_date
                            data['building_num'] = building_num
                            data['entry_did'] = entry_did
                            data['entry_time'] = entry_time

                            serializer = EntrySerializer(data=data)

                            if serializer.is_valid():  # 입력 data들 포맷 일치 여부 확인
                                serializer.save()

                        return JsonResponse({'msg': 'generate entry complete'}, status=201)
                    except Exception as e:
                        return JsonResponse({'msg': 'failed_Exception', 'error 내용': str(e)}, status=400)
                else:
                    tempadmindid = str(student.did_time_hash) + str(timestamp)
                    return JsonResponse({'msg': 'check_DID error', 'studentDidhash' : hashedData ,'adminDidhash' : hashlib.sha256(tempadmindid.encode('utf-8')).hexdigest()}, status=400)
            else:
                return JsonResponse({'msg': 'timestamp error'}, status=400)
        else:
            return JsonResponse({'msg': 'Key is error'}, status=400)


# 사용자 기준 출입 기록 GET
@csrf_exempt
def entry_list(request):
    if request.method == 'GET':
        if not 'entry_did' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)

        entry_did = request.GET.get('entry_did', None)
        entryDB = Entry.objects.filter(entry_did=entry_did)

        if len(entryDB) == 0:
            return JsonResponse({'msg': 'has no entry'}, status=400)

        json_data = {}
        json_data['entry'] = []

        for i in range(0, len(entryDB), 1):
            entry_data = {}
            entry_data['entry_date'] = entryDB[i].entry_date
            entry_data['building_num'] = entryDB[i].building_num
            entry_data['entry_did'] = entryDB[i].entry_did
            entry_data['entry_time'] = entryDB[i].entry_time

            json_data['entry'].append(entry_data)

        return JsonResponse(json_data, status=201) 


# 관리자 기준 출입 기록 GET(강의동 별)
@csrf_exempt
def entry_admin(request):
    if request.method == 'GET':
        if not 'building_num' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)
        if not 'page_num' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)
        if not 'order' in request.GET:
            return JsonResponse({'msg': 'parmas error'}, status=400)

        order_by = request.GET.get('order', None) # 오름차순, 내림차순 params GET
        building_num = request.GET.get('building_num', None)  # 강의동 번호 GET

        # 정렬 방식에 따라 DB 튜플 불러오기
        if order_by == 'Asc':
            entryDB = Entry.objects.filter(building_num=building_num).order_by('id')
        elif order_by == 'Desc':
            entryDB = Entry.objects.filter(building_num=building_num).order_by('-id')
        else:
            return JsonResponse({'msg': 'order param error'}, status=400)

        if len(entryDB) == 0:
            return JsonResponse({'msg': 'has no entry'}, status=400)

        # 페이지네이션 적용
        page_num = request.GET.get('page_num', None)
        paginator = Paginator(entryDB, 10)
        total_page = paginator.num_pages
        total_count = paginator.count
        posts_entry = paginator.get_page(page_num)

        # JSON 형태로 만들고, Response
        json_data = {'entry':'','total_page':'', 'total_count':total_count}
        json_data['entry'] = []
        json_data['total_page']= total_page
        json_data['total_count']= total_count

        for i in range(0, len(posts_entry), 1):
            entry_data = {}
            entry_data['entry_date'] = posts_entry[i].entry_date
            entry_data['building_num'] = posts_entry[i].building_num
            entry_data['entry_did'] = posts_entry[i].entry_did
            entry_data['entry_time'] = posts_entry[i].entry_time

            json_data['entry'].append(entry_data)

        return JsonResponse(json_data, status=201)
        

