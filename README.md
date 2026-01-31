# Zbiór punktów przecięcia dwóch odcinków (Geometria Obliczeniowa 2026)

Aplikacja w Pythonie z **interfejsem graficznym (Tkinter)**, która wyznacza przecięcie dwóch odcinków na płaszczyźnie:
- informuje, czy odcinki przecinają się (TAK/NIE),
- jeżeli tak, podaje **zbiór przecięcia**: pojedynczy **punkt** albo **odcinek** (z końcami).

Projekt jest przygotowany tak, aby można go było od razu uruchomić w **Visual Studio Code** oraz wrzucić na GitHub.

## Uruchomienie

Wymagania:
- Python 3.10+ (zalecane 3.11+)
- Tkinter (zwykle jest wbudowany w Python na Windows/macOS; na niektórych dystrybucjach Linux może wymagać doinstalowania)

### GUI
```bash
# Windows PowerShell
$env:PYTHONPATH="./src"; python -m segment_intersection

# Linux/macOS
PYTHONPATH=./src python -m segment_intersection
```

### Testy
```bash
# Windows PowerShell
$env:PYTHONPATH="./src"; python -m unittest -v tests.test_geometry

# Linux/macOS
PYTHONPATH=./src python -m unittest -v tests.test_geometry
```

## Funkcje aplikacji
- Ręczne wprowadzanie współrzędnych (pola tekstowe).
- Walidacja danych (liczby typu `int`/`float`, błąd wejścia nie powoduje crasha).
- Przeciąganie końców odcinków myszą na płótnie.
- Siatka współrzędnych, zoom (kółko myszy) i przesuwanie (środkowy przycisk / przeciąganie).
- Wynik przecięcia widoczny tekstowo i graficznie:
  - brak przecięcia,
  - punkt przecięcia,
  - część wspólna będąca odcinkiem.

## Struktura repozytorium
- `src/segment_intersection/` – kod aplikacji (GUI + geometria).
- `tests/` – testy jednostkowe algorytmu.
- `docs/` – dokumentacja projektu (DOCX).
- `.vscode/` – pomocnicza konfiguracja uruchamiania w VS Code.

## Licencja
Jeżeli potrzebujesz, możesz dodać własną (np. MIT). Domyślnie brak.
