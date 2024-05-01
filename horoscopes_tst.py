from posting.core.horoscopes_images import paste_horoscopes_rates
import django


if __name__ == '__main__':
    django.setup()
    paste_horoscopes_rates('horoscope.jpg', original_rates=7766)
