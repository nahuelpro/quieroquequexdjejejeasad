
import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


# CONFIGURACION
SERVER_NAME = "yo quiero una papa"

LOGIN_URL = "https://accounts.seedloaf.com/sign-in"

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")


def find_text(driver, text):
    """Busca un elemento que contenga exactamente el texto indicado."""
    elements = driver.find_elements(
        By.XPATH,
        f"//*[normalize-space(.)='{text}']"
    )

    for element in elements:
        if element.is_displayed():
            return element

    return False


def find_world_button(driver, button_text):
    """Busca un botón Start World o Stop World."""
    buttons = driver.find_elements(
        By.XPATH,
        f"//button[contains(normalize-space(.), '{button_text}')]"
    )

    for button in buttons:
        if button.is_displayed() and button.is_enabled():
            return button

    return False


def click_element(driver, element):
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        element
    )

    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


def login(driver, wait):

    if not USERNAME or not PASSWORD:
        raise RuntimeError("Faltan los Secrets USERNAME o PASSWORD.")

    driver.get(LOGIN_URL)

    # Correo
    email = wait.until(
        lambda d: d.find_element(By.ID, "identifier-field")
        if d.find_elements(By.ID, "identifier-field") else False
    )

    email.clear()
    email.send_keys(USERNAME)
    email.submit()

    print("Correo enviado.")

    # Contraseña
    password = WebDriverWait(driver, 30).until(
        lambda d: d.find_element(By.ID, "password-field")
        if d.find_elements(By.ID, "password-field") else False
    )

    password.clear()
    password.send_keys(PASSWORD)
    password.submit()

    print("Contraseña enviada.")

    # Esperar a que se complete el acceso.
    try:
        WebDriverWait(driver, 40).until(
            lambda d: "accounts.seedloaf.com" not in d.current_url
        )
    except TimeoutException:
        raise RuntimeError(
            "Seedloaf no terminó el inicio de sesión. "
            "Puede haber una verificación adicional."
        )

    print("Inicio de sesión completado.")


def open_shared_with_you(driver, wait):

    shared = wait.until(
        lambda d: find_text(d, "Shared With You")
    )

    click_element(driver, shared)

    print("Entrando a Shared With You.")

    wait.until(
        lambda d: find_text(d, SERVER_NAME)
    )

    print("Servidor encontrado en Shared With You.")


def open_server_if_needed(driver, wait):

    # Primero comprobar si los botones ya están disponibles.
    start = find_world_button(driver, "Start World")
    stop = find_world_button(driver, "Stop World")

    if not start and not stop:

        # Entrar en el servidor compartido.
        server = wait.until(
            lambda d: find_text(d, SERVER_NAME)
        )

        click_element(driver, server)

        print("Abriendo el servidor compartido.")

        wait.until(
            lambda d: (
                find_world_button(d, "Start World")
                or find_world_button(d, "Stop World")
            )
        )

    # Comprobar el estado.
    stop = find_world_button(driver, "Stop World")

    if stop:
        print("El servidor ya está encendido.")
        return

    start = find_world_button(driver, "Start World")

    if not start:
        raise RuntimeError(
            "No se encontró Start World ni Stop World."
        )

    print("Servidor apagado. Solicitando encendido.")

    click_element(driver, start)

    # Esperar confirmación visual del encendido.
    try:
        WebDriverWait(driver, 120).until(
            lambda d: find_world_button(d, "Stop World")
        )
    except TimeoutException:
        raise RuntimeError(
            "Se pulsó Start World, pero no apareció Stop World "
            "después de 120 segundos."
        )

    print("¡Servidor encendido correctamente!")


def main():

    options = Options()

    options.binary_location = "/opt/chrome/chrome"

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")

    driver = webdriver.Chrome(
        options=options,
        service=Service("/usr/local/bin/chromedriver")
    )

    try:
        wait = WebDriverWait(driver, 30)

        login(driver, wait)

        open_shared_with_you(driver, wait)

        open_server_if_needed(driver, wait)

        print("Proceso finalizado correctamente.")

    except Exception as error:

        print(f"ERROR: {type(error).__name__}: {error}")
        print(f"URL actual: {driver.current_url}")

        # Guardar una captura para diagnosticar el problema.
        try:
            driver.save_screenshot("seedloaf_error.png")
            print("Captura guardada: seedloaf_error.png")
        except Exception:
            pass

        sys.exit(1)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
