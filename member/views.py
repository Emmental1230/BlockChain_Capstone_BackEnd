from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from .models import Member
from .serializers import MemberSerializer
import subprocess
#import bcrypt
# Create your views here.


@csrf_exempt
def signup_request(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = MemberSerializer(data=data)
        #if pk == 'temporaryKey':  
        if serializer.is_valid():       #입력 data들 포맷 일치 여부 확인
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)



@csrf_exempt
def member_list(request):
    #모든 학생들 조회 or 새로운 학생 생성
    if request.method == 'GET':
        members = Member.objects.all()
        serializer = MemberSerializer(members, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = MemberSerializer(data=data)
        #if pk == 'temporaryKey':         #app사용자인지 확인
        if serializer.is_valid():       #입력 data들 포맷 일치 여부 확인
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)         



@csrf_exempt
def member(request, num):
    """
    학생 수정
    """
    obj = Member.objects.get(stdnum=num)

    if request.method == 'GET':
        serializer = MemberSerializer(obj)
        return JsonResponse(serializer.data, safe=False)
    
    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = MemberSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)  
    


@api_view(['GET'])
def run_python(request): 
    if request.method == 'GET': 
        command = ["python3","/Users/younggilpark/Desktop/Capstone/Capstone_younggil/backend/echo_test.py"]
        try: 
            process = Popen(command, stdout=PIPE, stderr=STDOUT) 
            output = process.stdout.read() 
            exitstatus = process.poll() 
            if (exitstatus==0): 
                    result = {"status": "Success", "output":str(output)} 
            else: 
                    result = {"status": "Failed", "output":str(output)}
        except Exception as e: 
            result =  {"status": "failed", "output":str(e)} 
        html = "<html><body>Script status: %s \n Output: %s</body></html>" %(result['status'],result['output']) 
        #return HttpResponse(html) 
        return Response(status=status.HTTP_200_OK)