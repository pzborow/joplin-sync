# joplin-sync

Proste dwukierunkowe synchronizowanie drzewa Markdown z Joplinem.

`joplin-sync` rozwiązuje problem pracy z notatkami Joplina jak z normalnym projektem plikowym. Joplin jest wygodny do czytania, organizowania i synchronizacji notatek między urządzeniami, ale przy większych materiałach technicznych często wygodniej edytować Markdown lokalnie: w VS Code, z wyszukiwaniem po plikach, diffem, testami linków, refaktoryzacją nazw i kontrolą wersji.

Narzędzie mapuje wybraną gałąź notatników Joplina na katalog lokalny:

- notebook Joplina staje się katalogiem,
- notatka staje się plikiem `.md`,
- podnotatniki stają się podkatalogami,
- linki między notatkami są konwertowane między formatem Joplina `:/note_id` i lokalnymi linkami Markdown.

Po stronie lokalnej katalog jest źródłem prawdy podczas `publish`: notatki brakujące w Joplinie są tworzone, istniejące aktualizowane, a notatki usunięte lokalnie są usuwane z Joplina.

## Use case'y

Typowe zastosowania:

- Pisanie większych serii notatek technicznych w edytorze kodu, a czytanie ich później w Joplinie.
- Praca nad dokumentacją kursu, cheatsheetem albo bazą wiedzy, gdzie liczą się lokalne diffy i szybka edycja wielu plików.
- Poprawianie linków, nazw plików i struktury folderów poza UI Joplina.
- Synchronizacja notatek z repozytorium Git bez ręcznego kopiowania treści między Joplinem i plikami.
- Praca z Joplinem uruchomionym na innym komputerze, na przykład przez tunel SSH do Web Clipper API.

To nie jest pełny system rozwiązywania konfliktów. Narzędzie zakłada świadomy workflow: najpierw `pull`, potem lokalna edycja, potem `publish`.

## Workflow

Najbezpieczniejszy cykl pracy:

```bash
mkdir moje-notatki
cd moje-notatki
joplin-sync pull --path "Programming/Elasticsearch"
```

Następnie edytujesz pliki lokalnie, sprawdzasz diff albo walidujesz linki, a na końcu publikujesz zmiany:

```bash
joplin-sync publish
```

Podczas `publish` narzędzie wypisuje ścieżkę notatnika oraz akcje dla poszczególnych notatek:

```text
publish notebook: Programming/Elasticsearch
update: Programming/Elasticsearch/01 Czym jest Elasticsearch
create: Programming/Elasticsearch/Deep dive/Nowa notatka
delete: Programming/Elasticsearch/Stara notatka
```

Identyfikatory notatek nie są trzymane w lokalnym state jako lista notatek. Przy publikacji `joplin-sync` pobiera aktualne mapowanie z Joplina po ścieżce folderu i tytule notatki, tworzy brakujące notatki, a dopiero potem aktualizuje treść i linki.

## Instalacja

Najprostsza instalacja z GitHuba przez `pipx`:

```bash
pipx install 'git+ssh://git@github.com/pzborow/joplin-sync.git'
```

Odinstalowanie:

```bash
pipx uninstall joplin-sync
```

Aktualizacja do najnowszej wersji z GitHuba:

```bash
pipx uninstall joplin-sync
pipx install 'git+ssh://git@github.com/pzborow/joplin-sync.git'
```

Sprawdzenie instalacji:

```bash
joplin-sync --help
pipx list
```

Do pracy nad kodem sklonuj repozytorium:

```bash
git clone git@github.com:pzborow/joplin-sync.git
cd joplin-sync
```

Lokalna instalacja developerska:

```bash
python3 -m pip install -e /ścieżka/do/joplin_sync
```

Jeżeli zmieniasz ostatni commit przed publikacją, użyj amend i bezpiecznego force push:

```bash
git add README.md src tests
git commit --amend --no-edit
git push --force-with-lease origin main
```

Usunięcie lokalnego klona po wypchnięciu zmian:

```bash
cd ..
rm -rf joplin-sync
```

Token może być w zmiennej `JOPLIN_TOKEN` albo w konfiguracji użytkownika:

```text
~/.config/joplin-sync/config
```

Format:

```text
JOPLIN_TOKEN=...
JOPLIN_URL=http://127.0.0.1:41184
```

`JOPLIN_URL` jest opcjonalny. Domyślnie używany jest `http://127.0.0.1:41184`. Możesz użyć innego pliku przez `--config` albo nadpisać adres przez `--url`. Zmienne środowiskowe `JOPLIN_TOKEN` i `JOPLIN_URL` mają pierwszeństwo.

## Połączenie z Joplinem przez odwrotny tunel SSH

Jeżeli Joplin działa na komputerze z Windows, a skrypt uruchamiasz na innym komputerze lub maszynie wirtualnej, uruchom tunel odwrotny na komputerze z Joplinem:

```bash
ssh -N -R 41184:127.0.0.1:41184 użytkownik@komputer-ze-skryptem
```

Na komputerze uruchamiającym skrypt ustaw:

```text
JOPLIN_URL=http://127.0.0.1:41184
```

Tunel musi pozostać aktywny podczas używania `joplin-sync`. Sprawdzenie połączenia:

```bash
joplin-sync list mongo
```

Token trzymaj w `~/.config/joplin-sync/config` albo w zmiennej `JOPLIN_TOKEN`; nie wpisuj go do README ani do repozytorium.

## Pull

Uruchom w pustym katalogu projektu:

```bash
mkdir moje-notatki
cd moje-notatki
joplin-sync pull --path Programming/Elasticsearch
```

`pull` pobiera całą gałąź rekurencyjnie. Foldery stają się podkatalogami, a notatki plikami `.md`. Stan zapisuje w `.joplin-sync.json`.

Jeżeli katalog nie jest pusty, operacja przerywa. `--force` usuwa jego zawartość przed pobraniem.

## Publish

```bash
joplin-sync publish
```

Bez `--path` używana jest ścieżka z `.joplin-sync.json`:

```bash
joplin-sync publish --path Programming/Elasticsearch --force
```

`publish` bez `--force` nie nadpisuje istniejącej gałęzi Joplina. `--force` jest jedynym potwierdzeniem nadpisania.

## List

```bash
joplin-sync list mongo
```

Wyszukiwanie ścieżek jest rekurencyjne i niewrażliwe na wielkość liter.

## Ostrzeżenie

To narzędzie celowo nie wykrywa konfliktów i nie wykonuje atomowej transakcji. `pull --force` zastępuje lokalne pliki, a `publish --force` może nadpisać notatki w Joplinie. Najpierw użyj `--force` tylko wtedy, gdy świadomie akceptujesz tę operację.

