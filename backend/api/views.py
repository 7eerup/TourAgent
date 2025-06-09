from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth.models import auth, User

from .models import Api

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Create your views here.
def index(request):
    return HttpResponse("Hello, world")

def login(request):
    return render(request, "auth/login.html")

def login_auth(request):
    if request.method == "GET":
        return HttpResponse("정상적인 접근이 아닙니다.")
    
    email = request.POST.get("email", "")
    password = request.POST.get("password", "")

    print("email :", email)
    print("password :", password)

    username = User.objects.get(email=email)

    # 로그인 인증
    user = authenticate(username=username, password=password)

    if user is not None:
        auth.login(request, user)
        # 로그인 성공
        return redirect("list")
    else:
        # 로그인 실패
        return HttpResponse("로그인 인증 실패")


@login_required(login_url="/accounts/login/")
def update_save(request):
    if request.method == "GET":
        return HttpResponse("정상적인 접근이 아닙니다.")
    
    # 받야야할 데이터
    # id, password, email, phone
    id = request.POST.get("id", "")
    old_password = request.POST.get("old_password", "")
    email = request.POST.get("email", "")
    phone = request.POST.get("phone", "")

    print("id :", id)
    print("password :", old_password)
    print("email :", email)
    print("phone :", phone)

    # 데이터를 수정하려면 id값이 일치하는 것만 수정
    try:
        memEdit = Api.objects.get(id=id, password=old_password)
    except:
        return HttpResponse("암호가 일치하지 않습니다.")

    # 수정
    memEdit.email = email
    memEdit.phone = phone
    memEdit.save()

    # 데이터 받아오기
    return redirect("list")


@login_required(login_url="/accounts/login/")
def update(request, idx):
    print("idx :", idx)

    # idx에 맞는 회원 정보를 가져온다.
    # (SQL) SELECT * FROM api_members WHERE id = idx
    try:
        memData = Api.objects.get(id=idx)
    except:
        # 에러처리
        return HttpResponse("회원정보가 존재하지 않습니다.")
    
    # print("SQL : ", memData.query)
    # 가져온 값 확인
    print("id :", memData.id)
    print("user_id :", memData.user_id)
    print("username :", memData.username)
    print("password :", memData.password)
    print("email :", memData.email)
    print("phone :", memData.phone_number)

    return render(request, "accounts/update.html", {"data":memData})


@login_required(login_url="/accounts/login/")
def delete(request, id):
    Api.objects.filter(id=id).delete()

    return redirect("list")


@login_required(login_url="/accounts/login/")
def list(request):
    AccountList = Api.objects.all().order_by("-id")
    print("SQL : ", AccountList.query)

    for user in AccountList:
        print("id :", user.id)
        print("user_id :", user.user_id)
        print("username :", user.username)
        print("password :", user.password)
        print("email :", user.email)
        print("phone :", user.phone_number)
        print("visit_count :", user.visit_count)
        print("joined_at :", user.joined_at)
        print("joined_ip :", user.joined_ip)

    return render(request, "accounts/list.html", {"data": AccountList})


@login_required(login_url="/accounts/login/")
def add(request):
    return render(request, "accounts/add.html")


@login_required(login_url="/accounts/login/")
def add_save(request):
    if request.method == "GET":
        return HttpResponse("정상적인 접근이 아닙니다.")
        
    user_id = request.POST.get("user_id", "")
    username = request.POST.get("username", "")
    password = request.POST.get("password", "")
    email = request.POST.get("email", "")
    phone = request.POST.get("phone", "")

    print("user_id :", user_id)
    print("username :", username)
    print("password :", password)
    print("email :", email)
    print("phone", phone)
    

    # 계정 등록
    save_account = Api()
    save_account.user_id = user_id
    save_account.username = username
    save_account.password = password
    save_account.email = email
    save_account.phone_number = phone
    save_account.visit_count = 0
    save_account.joined_at = None
    save_account.joined_ip = get_client_ip(request)
    save_account.save()

    return redirect("list")