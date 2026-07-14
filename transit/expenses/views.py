from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum
from .models import Expense
from .forms import ExpenseForm
from accounts.decorators import role_required

@role_required('Financial Analyst')
def expense_list(request):
    type_filter = request.GET.get('type', '')
    expenses = Expense.objects.all().order_by('-expense_date')

    if type_filter:
        expenses = expenses.filter(expense_type=type_filter)

    total_amount = expenses.aggregate(total=Sum('amount'))['total'] or 0

    paginator = Paginator(expenses, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'expenses/list.html', {
        'page_obj': page_obj,
        'type_filter': type_filter,
        'total_amount': total_amount,
        'type_choices': Expense.EXPENSE_TYPE_CHOICES
    })

@role_required('Financial Analyst')
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save()
            messages.success(request, f"Expense of {expense.amount} logged successfully.")
            return redirect('expense_list')
        else:
            messages.error(request, "Error logging expense. Check fields.")
    else:
        form = ExpenseForm()
    return render(request, 'expenses/form.html', {'form': form, 'title': 'Log Expense'})

@role_required('Financial Analyst')
def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense updated successfully.")
            return redirect('expense_list')
        else:
            messages.error(request, "Error updating expense.")
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'expenses/form.html', {'form': form, 'title': 'Edit Expense', 'expense': expense})

@role_required('Financial Analyst')
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, "Expense deleted successfully.")
        return redirect('expense_list')
    return render(request, 'expenses/confirm_delete.html', {'expense': expense})
