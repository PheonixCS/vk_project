import logging

from celery import shared_task

from posting.models import Group
from scraping.core.helpers import get_tomorrow_date_ru
from scraping.core.horoscopes import fetch_zodiac_sign, horoscopes_translate, save_horoscope_record_to_db
from services.horoscopes.mailru import MailRuHoroscopes, WomenHoroscopes

log = logging.getLogger('scraping.scheduled')


@shared_task(time_limit=180, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3}, retry_backoff=120)
def parse_horoscopes() -> None:
    log.debug('start parse_horoscopes')
    horoscope_page = MailRuHoroscopes()
    women_horoscopes = WomenHoroscopes()

    tomorrow_date_ru = get_tomorrow_date_ru()
    log.debug(f'tomorrows date in ru is {tomorrow_date_ru}')

    parsed = horoscope_page.parse()
    log.debug(f'parsed {len(parsed)} horoscopes')

    groups_with_horoscope_posting = Group.objects.filter(
        group_type__in=(Group.HOROSCOPES_MAIN, Group.HOROSCOPES_COMMON))
    log.debug(f'got {len(groups_with_horoscope_posting)} groups for posting')

    for group in groups_with_horoscope_posting:
        group_sign_ru = fetch_zodiac_sign(group.name)
        log.debug(f'Group {group} got sign: "{group_sign_ru}"')
        if group_sign_ru:
            group_sign_en = horoscopes_translate(group_sign_ru, to_lang='en')
            if group_sign_en not in parsed.keys():
                log.warning(f'{group_sign_en} not in {parsed.keys()}')
                continue
            else:
                additional_text = f'{tomorrow_date_ru}, {group_sign_ru}'
                record_text = f'{additional_text}\n{parsed[group_sign_en]}'
                save_horoscope_record_to_db(group, record_text, group_sign_en)

    log.debug('start craping horoscopes for women')
    parsed = women_horoscopes.parse(by_selector=True)
    women_horoscopes_group = Group.objects.get(group_id=29038248)

    for sign, value in parsed.items():
        additional_text = f'{tomorrow_date_ru}, {sign}'
        record_text = f'{additional_text}\n{value}'
        save_horoscope_record_to_db(women_horoscopes_group, record_text, sign)

    log.debug('end craping horoscopes for women')

    log.debug('finish parse_horoscopes')
