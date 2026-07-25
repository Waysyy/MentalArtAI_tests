import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect, Page
import re

def test_smoke_pipeline(page: Page):

    is_login_mode = True

    page.goto('https://mentalartai.ru/')
    # login = page.get_by_title('Войти')

    # Ищем кнопку входа на главной странице и кликаем
    login_btn = page.locator(".login-icon-btn")
    expect(login_btn).to_be_enabled()
    print(login_btn)
    login_btn.click()

    if not is_login_mode:
        # На странице авторизации ищем кнопку регистрация
        registration_switch_btn = page.get_by_role("button", name="Регистрация")
        expect(registration_switch_btn).to_be_visible()
        print(registration_switch_btn)
        registration_switch_btn.click()

        # Скроллим до конца формы
        consent_modal = page.locator(".consent-modal")
        expect(consent_modal).to_be_visible()
        consent_modal.scroll_into_view_if_needed()
        print(consent_modal)

        # Помечаем чекбоксы
        checkmarks = page.locator(".checkmark").all()
        for checkmark in checkmarks:
            expect(checkmark).to_be_visible()
            checkmark.check()

        # Принимаем соглашение
        consent_btn_accept = page.get_by_role("button", name="Принять и продолжить")
        expect(consent_btn_accept).not_to_be_disabled()
        consent_btn_accept.click()

        # Заполняем пароль
        password_placeholder = page.get_by_placeholder("Придумайте пароль")
        password_repeat_placeholder = page.get_by_placeholder("Повторите пароль")

        expect(password_repeat_placeholder).to_be_visible()
        expect(password_placeholder).to_be_visible()

        password_placeholder.fill("Test12345679!")
        password_repeat_placeholder.fill("Test12345679!")

        # Регистрируемся
        create_profile_btn = page.get_by_role("button", name="Создать профиль")
        expect(create_profile_btn).to_be_enabled()
        create_profile_btn.click()
    else:
        # Авторизуемся
        login_placeholder = page.get_by_placeholder("Логин")
        password_placeholder = page.get_by_placeholder("Пароль")

        expect(login_placeholder).to_be_visible()
        expect(password_placeholder).to_be_visible()

        login_placeholder.fill("user_dy6a9ord")
        password_placeholder.fill("Test12345679!")

        login_profile_btn = page.get_by_role("main").get_by_role("button", name="Войти в аккаунт")
        expect(login_profile_btn).to_be_visible()
        login_profile_btn.click()

    take_test_btn = (page.get_by_role("button", name="Пройти тест")).first

    # Ждем загрузку
    expect(page).to_have_url("https://mentalartai.ru/profile")
    expect(take_test_btn).to_be_visible()
    take_test_btn.click()

    # Выбираем тест
    choice_test = page.get_by_alt_text("Пройти психологический тест Рисунок человека онлайн")
    expect(choice_test).to_be_visible()
    choice_test.click()

    # Ждем загрузки страницы инструкции
    expect(page).to_have_url(re.compile(r"https://mentalartai\.ru/instructions/.*"))

    # Заполняем combobox
    input_wrapper_categories = page.locator(".name-input")
    input_wrapper_age = page.locator(".age-input")
    input_wrapper_gender = page.locator(".gender-select")

    expect(input_wrapper_categories).to_be_visible()
    expect(input_wrapper_gender).to_be_visible()
    expect(input_wrapper_age).to_be_visible()

    input_wrapper_categories.select_option(label="Личное")
    input_wrapper_age.select_option(label="5-10 лет")
    input_wrapper_gender.select_option(label="Мужской")

    # Клик на выполнение теста
    test_began_btn = page.get_by_role("button", name="Начать выполнение теста")

    expect(test_began_btn).to_be_visible()
    test_began_btn.click()

    # Ждем загрузки страницы загрузки
    expect(page).to_have_url(re.compile(r"https://mentalartai\.ru/load-image/.*"))
    page.wait_for_load_state("networkidle")

    # Загружаем файл
    load_image_input = page.locator("input")

    img_path = str(Path("uploads") / "26181120-4a4b-4ecd-8fb8-717be52bbeda.png")
    load_image_input.set_input_files(img_path)

    # Ждем загрузки страницы результата
    expect(page).to_have_url(re.compile(r"https://mentalartai\.ru/result/.*"), timeout=30000)

    # Генерируем и скачиваем отчет
    download_report_btn = page.get_by_title("Скачать отчет в PDF")
    expect(download_report_btn).to_be_visible()

    with page.expect_download() as download_info:
        download_report_btn.click()

    download = download_info.value
    save_path = Path("downloads") / download.suggested_filename
    download.save_as(str(save_path.resolve()))

    assert save_path.exists()

