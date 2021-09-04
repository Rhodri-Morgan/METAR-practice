from django.shortcuts import render, redirect

from metar_tester.metar_collector import METAR_colllector


def begin_test(request):
    '''
    status = None
    icao = None
    data = None
    questions = None
    already_asked = None

    try:
        status = request.session['status']
        icao = request.session['icao']
        data = request.session['data']
        questions = request.session['questions']
        already_asked = request.session['already_asked']

        if len(questions) == len(already_asked):                                # Ran out of qustions refresh
            raise Exception('Ran out of questions, need to regenerate')
    except Exception:
        metar_collector = METAR_colllector()
        status, icao, data, questions = metar_collector.get_package()
        already_asked = []


    if status == 200:
        print('TODO implement normal page')
    elif status == 503:
        print('TODO implement page saying API is down')
    else:
        print('TODO implement page saying API error has occured')

    '''
    data = {
        'title': 'METAR Tester - Begin'
    }
    return render(request, 'metar_tester/begin.html', data)
