from .models import Member
from .models import Entry
from rest_framework import serializers, viewsets

class MemberSerializer(serializers.ModelSerializer):    #data를 json형태로 바꿔준다.

    class Meta:
        model = Member
        fields = '__all__'

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

class EntrySerializer(serializers.ModelSerializer):    #data를 json형태로 바꿔준다.

    class Meta:
        model = Entry
        fields = '__all__'

class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer

