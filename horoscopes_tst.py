from services.horoscopes.mailru import WomenHoroscopes

if __name__ == '__main__':
    horoscope = WomenHoroscopes().parse(by_selector=True)
    print(horoscope['arises'])
