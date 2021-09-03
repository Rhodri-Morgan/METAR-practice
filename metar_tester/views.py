from django.shortcuts import render, redirect

def begin_test(request):

    

    data = {
        'title': 'METAR Tester - Begin'
    }
    return render(request, 'metar_tester/begin.html', data)
