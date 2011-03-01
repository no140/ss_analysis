# plot primary parameter logs

import numpy as np
import dateutil.parser
import matplotlib.dates
import matplotlib.pyplot as plt
import datetime
import os.path

usecols = [0,5,6,7,8,9]
plotColorList  = ['b', 'r', 'g', 'k', 'b', 'r', 'g', 'k', 'b', 'r', 'g', 'k']
plotSymbolList  = ['x', 'x', 'x', 'x', 's', 's', 's', 's', 'd', 'd', 'd', 'd']
dateStart = datetime.datetime(2011,  1,  1)
dateEnd   = datetime.datetime(2011,  2,  28)

def creditScrub(val):
    ''' take out values of None from the data on import '''
    if val=='None':
        return 0.0
    else:
        val = float(val)
        if val < 0:
            val = 0
        return val

def getDataAsRecordArray():
    '''
    load csv from shared solar gateway and create
    numpy record array
    '''
    dtype = [('watthours',   'float'),      # column 0
             ('circuit_id',  'int'),        # column 5
             ('use_time',    'float'),      # column 6
             ('credit',      'float'),      # column 7
             ('circuit',     'S30'),        # column 8
             ('date',        'object')]     # column 9
    dtype = np.dtype(dtype)

    # either get file from web or use existing file on computer
    fileName = 'dataFile.csv'
    if os.path.isfile(fileName):
        # file exists so loadtxt uses csv file
        print 'loading', fileName
        print 'new data is _NOT_ being downloaded'
        print 'remove dataFile.csv to download fresh data'
        dataStream = open(fileName, 'r')
    else:
        # file does not exist so we must download it
        print 'opening url'
        import urllib
        dataString = urllib.urlopen('http://178.79.140.99/sys/export?model=PrimaryLog').read()

        print 'converting to cStringIO'
        import cStringIO
        dataStream = cStringIO.StringIO(dataString)

        # dump csv data to file
        f = open('dataFile.csv','w')
        f.write(dataString)
        f.close()

    print 'np.loadtxt'
    # load file
    d = np.loadtxt(dataStream, delimiter=',',
                               skiprows=1,
                               dtype = dtype,
                               converters = {7: creditScrub,
                                             9: dateutil.parser.parse},
                               usecols=usecols)

    # sort by date
    sortIndex = d['date'].argsort()
    d = np.take(d, sortIndex)

    return d

def plotCreditSeparateAxes(d, dateStart, dateEnd):
    '''
    plots the credit in each circuit account on a separate axis
    '''
    fig = plt.figure(figsize=(8,12))
    circuits = set(d['circuit_id'])
    circuits = range(13,25)
    d = d[(d['date'] > dateStart) & (d['date'] < dateEnd)]
    for i,c in enumerate(circuits):
        # assemble data by circuit
        circuitMask = d['circuit_id'] == c
        dates = matplotlib.dates.date2num(d[circuitMask]['date'])
        credit = d[circuitMask]['credit']

        # plot individual circuit data
        if i == 0:
            ax = fig.add_axes((0.15,0.1+i*0.072,0.7,0.05))
        else:
            ax = fig.add_axes((0.15,0.1+i*0.072,0.7,0.05))
        ax.plot_date(dates, credit, '-x')
        ax.text(1.05, 0.4, c, transform = ax.transAxes)
        ax.set_yticks((0,500,1000))
        oldax = ax
        ax.set_ylim((0,1000))
        dateFormatter = matplotlib.dates.DateFormatter('%m-%d')
        ax.xaxis.set_major_formatter(dateFormatter)
        if i==0:
            ax.set_xlabel('Date')
        if i!=0:
            ax.set_xticklabels([])

    fig.text(0.05, 0.7, 'Account Credit (FCFA)', rotation='vertical')
    fig.suptitle('Account Credit in Pelengana')
    fig.savefig('plotCreditSeparateAxes.pdf')

def plotRecharges(d, dateStart, dateEnd):
    '''
    plots recharge events and outputs statistics on recharges
    '''
    d = d[(d['date'] > dateStart) & (d['date'] < dateEnd)]

    recharge = []
    circuits = range(13,25)

    for i,c in enumerate(circuits):
        circuitMask = d['circuit_id'] == c
        dates = d[circuitMask]['date']
        credit = d[circuitMask]['credit']

        # pull out recharge events
        cd = np.diff(credit)
        cmask = cd > 0
        circuitRecharges = zip(dates[cmask],cd[cmask])

        for element in circuitRecharges:
            if (element[0] != datetime.datetime(2011, 2, 22, 19, 45, 31) and
                element[1] > 100):
                recharge.append((matplotlib.dates.date2num(element[0]), element[1], c, element[0]))

    recharge = np.array(recharge)

    # print to console the recharge events
    for event in recharge:
        print event[3], str(event[1]).rjust(8), str(event[2]).rjust(4)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(recharge[:,0], recharge[:,2]-12, s=recharge[:,1]/10,
                                                edgecolor = 'b',
                                                facecolor = 'None',
                                                color = 'None')
    ax.grid(True)
    ax.xaxis_date()
    ax.set_xlabel('Date')
    ax.set_ylabel('Circuit')
    ax.set_ylim((0,13))
    ax.set_yticks(range(1,13))
    ax.set_title('Recharge Purchases in Pelengana')
    fig.savefig('plotRecharges.pdf')

def plotHouseholdEnergyPerHour(d, dateStart, dateEnd):
    '''
    plots a time series of accumulated watt hours
    for each circuit
    '''
    fig = plt.figure(figsize=(8,12))
    #ax = fig.add_axes((0.15,0.2,0.7,0.7))

    circuits = set(d['circuit_id'])
    circuits = range(13,25)

    d = d[(d['date'] > dateStart) & (d['date'] < dateEnd)]

    for i,c in enumerate(circuits):
        mask = d['circuit_id']==c
        dates = d[mask]['date']
        dates = matplotlib.dates.date2num(dates)
        wh = d[mask]['watthours']

        ax = fig.add_axes((0.15,0.1+i*0.072,0.7,0.05))


        # plot masked data to get date range
        ax.plot_date(dates, wh, '-x')
        if i==0:
            ax.set_xlabel('Date')
        if i!=0:
            ax.set_xticklabels([])

        ax.text(1.05, 0.4, c, transform = ax.transAxes)
        ax.set_ylim((0,150))
        ax.set_yticks((0,50,100,150))
        dateFormatter = matplotlib.dates.DateFormatter('%m-%d')
        ax.xaxis.set_major_formatter(dateFormatter)

    #fig.autofmt_xdate()
    fig.text(0.05,0.7, 'Energy Consumption (Watt-Hours)', rotation='vertical')
    fig.suptitle('Hourly Accumulated Consumption Per Household')
    fig.savefig('plotHouseholdEnergyPerHour.pdf')

def plotColloquium(d):
    '''
    plots a time series of accumulated watt hours
    for each circuit
    '''
    fig = plt.figure()
    #ax = fig.add_axes((0.15,0.2,0.7,0.7))

    circuits = set(d['circuit_id'])
    circuits = [17,23]
    for i,c in enumerate(circuits):
        mask = d['circuit_id']==c
        dates = d[mask]['date']
        dates = matplotlib.dates.date2num(dates)
        wh = d[mask]['watthours']

        plotHeight = 0.7 / len(circuits)
        ax = fig.add_axes((0.15, 0.1+i*(plotHeight+0.05), 0.7, plotHeight))


        # plot masked data to get date range
        ax.plot_date(dates, wh, '-x')
        if i==0:
            ax.set_xlabel('Date')
        if i!=0:
            ax.set_xticklabels([])

        ax.text(1.05, 0.4, c, transform = ax.transAxes)
        ax.set_ylim((0,150))
        ax.set_yticks((0,50,100,150))
        dateFormatter = matplotlib.dates.DateFormatter('%m-%d')
        ax.xaxis.set_major_formatter(dateFormatter)

    #fig.autofmt_xdate()
    fig.text(0.05,0.7, 'Energy Consumption (Watt-Hours)', rotation='vertical')
    fig.suptitle('Hourly Accumulated Consumption Per Household')
    fig.savefig('plotColloquium.pdf')

def plotHouseholdEnergyPerDay(d):
    '''
    plan:

    change to stacked plot
    place watt-hour data in numpy array

    '''
    mask = []
    for date in d['date']:
        if date.hour==23:
            mask.append(True)
        else:
            mask.append(False)

    mask = np.array(mask)
    d = d[mask]

    circuits = set(d['circuit_id'])
    fig = plt.figure()
    ax = fig.add_axes((0.15,0.2,0.7,0.7))


    for i,c in enumerate(circuits):
        mask = d['circuit_id']==c
        dates = d[mask]['date']
        print dates
        print 'date length', len(dates)
        dates = matplotlib.dates.date2num(dates)
        wh = d[mask]['watthours']
        print 'wh length', len(wh)

        # plot masked data to get date range
        ax.plot_date(dates, wh, '-o', label=str(c),
                                   color = plotColorList[i],
                                   marker = plotSymbolList[i],
                                   markeredgecolor = plotColorList[i],
                                   markerfacecolor = 'None')

    dateFormatter = matplotlib.dates.DateFormatter('%m-%d')
    ax.xaxis.set_major_formatter(dateFormatter)
    fig.autofmt_xdate()
    ax.legend(loc=(1.0,0.0))
    ax.grid(True)
    ax.set_xlabel('Date')
    ax.set_ylabel('Energy Consumed (Watt-Hours)')
    ax.set_title('Daily Consumption Per Household')
    fig.savefig('plotHouseholdEnergyPerDay.pdf')

def plotAllWattHours(d):
    # fixme: this function has plot points that don't make sense
    '''
    for each date in d, sum watt hours and report
    '''
    # yank non-pelengana customer circuits
    d = d[d['circuit_id']!=25]     #MAINS pelengana
    d = d[d['circuit_id']!=28]
    d = d[d['circuit_id']!=29]
    d = d[d['circuit_id']!=30]

    dates = set(d['date'])

    plotDates = np.array([])
    plotWattHours = np.array([])

    for date in dates:
        sum = d[d['date']==date]['watthours'].sum()
        plotDates = np.append(plotDates, date)
        plotWattHours = np.append(plotWattHours, sum)

    plotDates = matplotlib.dates.date2num(plotDates)

    sortIndices = plotDates.argsort()
    wh = np.take(plotWattHours, sortIndices)
    plotDates.sort()

    fig = plt.figure()
    ax = fig.add_subplot(111)

    plt.plot_date(plotDates, wh, '-')
    dateFormatter = matplotlib.dates.DateFormatter('%m-%d')
    ax.xaxis.set_major_formatter(dateFormatter)
    fig.autofmt_xdate()

    ax.grid()
    ax.set_xlabel('Date')
    ax.set_ylabel('Energy (Watt-Hours)')
    ax.set_title('Cumulative Energy Consumed (Reset Daily)')
    fig.savefig('plotAllWattHours.pdf')

def plotTotalEnergyPerDay(d):
    '''
    plot energy consumed by all circuits for each day
    not including mains
    '''
    mask = []
    for date in d['date']:
        if date.hour==23:
            mask.append(True)
        else:
            mask.append(False)

    mask = np.array(mask)
    d = d[mask]

    dates = set(d['date'])

    plotDates = np.array([])
    plotWattHours = np.array([])

    for date in dates:
        sum = d[d['date']==date]['watthours'].sum()
        plotDates = np.append(plotDates, date)
        plotWattHours = np.append(plotWattHours, sum)

    sortIndices = plotDates.argsort()
    plotWattHours = np.take(plotWattHours, sortIndices)
    plotDates.sort()

    plotDates = matplotlib.dates.date2num(plotDates)


    fig = plt.figure()
    ax = fig.add_subplot(111)

    plt.plot_date(plotDates, plotWattHours, 'ok')
    dateFormatter = matplotlib.dates.DateFormatter('%m-%d')
    ax.xaxis.set_major_formatter(dateFormatter)
    fig.autofmt_xdate()

    ax.grid()
    ax.set_xlabel('Date')
    ax.set_ylabel('Energy (Watt-Hours)')
    ax.set_ylim(bottom=0)
    ax.set_title('Total Household Energy Consumed Per Day')

    fig.savefig('plotTotalWattHoursPerDay.pdf')

def plotAveragedHourlyEnergy(energy, dateStart, dateEnd):
    numCircuits = energy.shape[0]
    numDays     = energy.shape[1]
    numHours    = energy.shape[2]

    fig = plt.figure(figsize=(8,12))

    for i,c in enumerate(range(numCircuits)):
        ax = fig.add_axes((0.15,0.05+i*0.072,0.7,0.05))

        henergy = np.diff(energy[c], axis=1)
        henergy = np.hstack((energy[c, :, 0].reshape(numDays,1),henergy))

        for day in range(numDays):
            ax.plot(henergy[day],color='#dddddd')

        ax.plot(sum(henergy,0)/numDays,'k')
        ax.set_ylim((-5,50))
        ax.set_yticks((0,25,50))
        ax.set_xlim((0,23))
        ax.set_xticks((0,4,8,12,16,20,23))
        ax.text(1.05, 0.4, str(c+13), transform = ax.transAxes)
        ax.grid(True)
    fig.text(0.05, 0.7, 'Power Usage (W)', rotation='vertical')
    fig.suptitle('averaged power usage\n'+str(dateStart)+'\n'+str(dateEnd))
    fig.savefig('plotAveragedHourlyEnergy.pdf')

def plotAveragedAccumulatedHourlyEnergy(energy, dateStart, dateEnd):
    numCircuits = energy.shape[0]
    numDays     = energy.shape[1]
    numHours    = energy.shape[2]

    fig = plt.figure(figsize=(8,12))

    for i,c in enumerate(range(numCircuits)):
        ax = fig.add_axes((0.15,0.05+i*0.072,0.7,0.05))

        for day in range(numDays):
            ax.plot(energy[c, day, :],color='#dddddd')

        ax.plot(sum(energy[c],0)/numDays,'k')
        ax.set_ylim((0,150))
        ax.set_yticks((0,50,100,150))
        ax.set_xlim((0,23))
        ax.set_xticks((0,4,8,12,16,20,23))
        ax.text(1.05, 0.4, str(c+13), transform = ax.transAxes)
        ax.grid(True)
    fig.text(0.05, 0.7, 'Accumulated Energy Use (Wh)', rotation='vertical')
    fig.suptitle('averaged accumulated usage\n'+str(dateStart)+'\n'+str(dateEnd))
    fig.savefig('plotAveragedAccumulatedHourlyEnergy.pdf')

def sampleHourlyWatthours(d, dateStart, dateEnd):
    # returns a 3rd rank tensor of data

    # initialize array
    circuits = range(13,25)
    numCircuits = len(circuits)
    numDays = (dateEnd - dateStart).days
    numHours = 24
    energy = np.zeros((numCircuits, numDays, numHours))

    # roundoff dates
    date = [datetime.datetime(dt.year, dt.month, dt.day, dt.hour) for dt in d['date']]
    date = np.array(date)

    dateCurrent = dateStart
    dateIndex = 0
    while dateCurrent != dateEnd:
        data = d[date==dateCurrent]
        hourIndex = dateCurrent.hour
        print dateCurrent,
        for i,c in enumerate(circuits):
            circuitIndex = c - circuits[0]
            loopData = data[data['circuit_id']==c]
            if loopData.shape == (0,):
                energy[circuitIndex, dateIndex, hourIndex] = energy[circuitIndex, dateIndex, hourIndex-1]
                print ' -',
            elif loopData.shape[0] > 1:
                energy[circuitIndex, dateIndex, hourIndex] = energy[circuitIndex, dateIndex, hourIndex-1]
                print ' +',
            else:
                energy[circuitIndex, dateIndex, hourIndex] = loopData['watthours']
                print c,
        print
        dateCurrent += datetime.timedelta(hours=1)
        if dateCurrent.hour == 0:
            dateIndex += 1

    return energy

print('Begin Load Data')
d = getDataAsRecordArray()
print('End Load Data')
#plotHouseholdEnergyPerDay(d)
#plotTotalEnergyPerDay(d)
#plotRecharges(d)
#plotColloquium(d)

dateStart = datetime.datetime(2011,  1,  1)
dateEnd   = datetime.datetime(2011,  4,  1)
plotCreditSeparateAxes(d, dateStart, dateEnd)
plotHouseholdEnergyPerHour(d, dateStart, dateEnd)

dateStart = datetime.datetime(2011,  2,  23)
dateEnd   = datetime.datetime(2011,  3,  1)
energy = sampleHourlyWatthours(d, dateStart, dateEnd)
plotAveragedAccumulatedHourlyEnergy(energy, dateStart, dateEnd)
plotAveragedHourlyEnergy(energy, dateStart, dateEnd)
