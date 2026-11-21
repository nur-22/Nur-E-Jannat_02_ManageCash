from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.views.decorators.http import require_POST
from decimal import Decimal
from .models import AddCash, Expense
from .forms import RegisterForm, AddCashForm, ExpenseForm, LoginForm

# Create your views here.
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful.')
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        user_obj = User.objects.filter(email__iexact=username).first()

        if user_obj:
            username = user_obj.username

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')

        form.add_error(None, 'Invalid username/email or password.')

    return render(request, 'login.html', {'form': form})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    income = AddCash.objects.filter(user=request.user
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    expenses = Expense.objects.filter(user=request.user
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    transactions = []

    for item in AddCash.objects.filter(user=request.user):
        transactions.append({
            'type': 'Income',
            'description': item.source,
            'amount': item.amount,
            'datetime': item.datetime,
        })

    for item in Expense.objects.filter(user=request.user):
        transactions.append({
            'type': 'Expense',
            'description': item.description,
            'amount': item.amount,
            'datetime': item.datetime,
        })

    transactions.sort(key=lambda item: item['datetime'], reverse=True)

    return render(request, 'dashboard.html', {
        'income': income,
        'expenses': expenses,
        'balance': income - expenses,
        'transactions': transactions[:10],
    })


@login_required
def add_cash(request):
    if request.method == 'POST':
        form = AddCashForm(request.POST)

        if form.is_valid():
            cash = form.save(commit=False)
            cash.user = request.user
            cash.save()

            messages.success(request, 'Cash added successfully.')
            return redirect('dashboard')
    else:
        form = AddCashForm()

    return render(request, 'transaction.html', {'form': form, 'title': 'Add Cash'})


@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)

        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()

            messages.success(request, 'Expense added successfully.')
            return redirect('dashboard')
    else:
        form = ExpenseForm()

    return render(request, 'transaction.html', {'form': form, 'title': 'Add Expense'})


@login_required
def profile_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        if not email:
            messages.error(request, 'Email is required.')

        elif User.objects.filter(email__iexact=email
        ).exclude(pk=request.user.pk).exists(): messages.error(request, 'Email is already in use.')

        else:
            request.user.email = email
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()

            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')

    return render(request, 'profile.html')