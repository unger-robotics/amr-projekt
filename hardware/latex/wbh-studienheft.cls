% =============================================================================
%  wbh-studienheft.cls
% =============================================================================
%  LaTeX-Klasse für WBH-Studienhefte
%  Satzparameter extrahiert aus ING01-L_0721N01.pdf (PyMuPDF-Analyse)
%
%  Verwendung:  \documentclass{wbh-studienheft}
%
%  Pflicht-Metadaten (im Dokument setzen):
%    \modulkuerzel{ING01-L}
%    \modultitel{Einführungsprojekt ...}
%    \modulversion{0721N01}
%    \autorname{Nachname, Vorname}
%    \matrikelnr{123456}
%
%  Optionale Kommandos:
%    \maketitlepage          – erzeugt Titelseite
%    \makecopyrightpage      – erzeugt Impressumsseite
%    \wbhvorwort{Text}       – Vorwort ohne Nummerierung
% =============================================================================
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{wbh-studienheft}[2025/03/04 v1.0 WBH-Studienheft-Klasse]

% ---------------------------------------------------------------------------
%  Klassenoptionen an KOMA-Script durchreichen
% ---------------------------------------------------------------------------
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{scrreprt}}
\ProcessOptions\relax

\LoadClass[
  fontsize=11.5pt,        % Fließtext lt. PDF-Analyse
  paper=a4,
  parskip=half,           % Absatzabstand statt Einzug
  headings=normal,
  toc=flat,
  numbers=noenddot,
  listof=totoc,
  bibliography=totoc
]{scrreprt}

% ===========================  Sprache & Kodierung  =========================
\RequirePackage[ngerman]{babel}
\RequirePackage[utf8]{inputenc}
\RequirePackage[T1]{fontenc}

% ===========================  Schriften  ===================================
% Fließtext: Linux Libertine (≈ LinLibertineUni im Original-PDF)
\RequirePackage{libertine}
\RequirePackage[libertine]{newtxmath}

% Überschriften: Helvetica ≈ Arial (Sans-Serif im Original)
\RequirePackage[scaled=0.92]{helvet}

% Sans-Serif für alle Gliederungsüberschriften
\addtokomafont{disposition}{\sffamily\bfseries}

% Kapitelüberschrift: 14 pt (gemessen)
\addtokomafont{chapter}{\fontsize{14pt}{16.8pt}\selectfont}

% Abschnittsüberschrift: 12 pt (gemessen)
\addtokomafont{section}{\fontsize{12pt}{14.4pt}\selectfont}

% Unterabschnitt: 11,5 pt fett + sans
\addtokomafont{subsection}{\fontsize{11.5pt}{13.5pt}\selectfont}

% Kapitelformat: Nummer + Titel ohne Präfix „Kapitel"
\renewcommand*{\chapterformat}{\thechapter\enskip}

% ===========================  Zeilenabstand  ===============================
% Gemessen: 13,5 pt bei 11,5 pt Schriftgröße → Faktor 1,17
% LaTeX: baselineskip = fontsize × \baselinestretch × 1,2
%        11,5 × 1,069 × 1,2 ≈ 13,5 pt
\RequirePackage{setspace}
\setstretch{1.069}

% ===========================  Seitengeometrie  =============================
\RequirePackage[
  left=30mm,
  right=25mm,
  top=25mm,
  bottom=25mm,
  headheight=14pt,
  headsep=12pt,
  footskip=20pt
]{geometry}

% ===========================  Farben  ======================================
\RequirePackage{xcolor}
\definecolor{wbhblau}{RGB}{0,120,190}

% ===========================  Kopf-/Fußzeile  ==============================
\RequirePackage[headsepline]{scrlayer-scrpage}
\clearpairofpagestyles

% Werden nach \begin{document} gesetzt, sobald Metadaten definiert sind
\AtBeginDocument{%
  \lohead{\footnotesize\sffamily\wbh@modulkuerzel}%
  \rohead{\footnotesize\sffamily\wbh@copyrightzeile}%
  \lofoot{\footnotesize\sffamily\wbh@modulkuerzel}%
  \rofoot{\footnotesize\sffamily\pagemark}%
  \pagestyle{scrheadings}%
}

% ===========================  Standardpakete  ==============================
\RequirePackage{graphicx}
\RequirePackage{booktabs}
\RequirePackage{tabularx}
\RequirePackage{float}
\RequirePackage{caption}
\RequirePackage{subcaption}
\RequirePackage{enumitem}
\RequirePackage{hyperref}
\RequirePackage{cleveref}

% Hyperlinks
\AtBeginDocument{%
  \hypersetup{
    colorlinks  = true,
    linkcolor   = wbhblau,
    citecolor   = wbhblau,
    urlcolor    = wbhblau,
    pdftitle    = {\wbh@modultitel},
    pdfauthor   = {\wbh@autorname}
  }%
}

% Abbildungs-/Tabellenbeschriftungen: kleiner, serifenlos
\captionsetup{
  font       = {small,sf},
  labelfont  = {bf},
  format     = plain,
  labelsep   = colon
}

% ===========================  Metadaten-Interface  =========================
% Interne Speicher
\newcommand{\wbh@modulkuerzel}{MODUL}
\newcommand{\wbh@modultitel}{Modultitel}
\newcommand{\wbh@modulversion}{0000N00}
\newcommand{\wbh@autorname}{Autor}
\newcommand{\wbh@matrikelnr}{000000}

% Öffentliche Setter
\newcommand{\modulkuerzel}[1]{\renewcommand{\wbh@modulkuerzel}{#1}}
\newcommand{\modultitel}[1]{\renewcommand{\wbh@modultitel}{#1}}
\newcommand{\modulversion}[1]{\renewcommand{\wbh@modulversion}{#1}}
\newcommand{\autorname}[1]{\renewcommand{\wbh@autorname}{#1}}
\newcommand{\matrikelnr}[1]{\renewcommand{\wbh@matrikelnr}{#1}}

% Copyrightzeile (automatisch zusammengesetzt)
\newcommand{\wbh@copyrightzeile}{%
  \textcopyright\ HfB, \today, \wbh@autorname\ (\wbh@matrikelnr)%
}

% ===========================  Titelseite  ==================================
\newcommand{\maketitlepage}{%
  \begin{titlepage}
    \sffamily
    \vspace*{4cm}
    {\Large \wbh@modulkuerzel\par}
    \vspace{1cm}
    {\LARGE\bfseries \wbh@modultitel\par}
    \vspace{1cm}
    {\large \wbh@modulversion\par}
    \vspace{2cm}
    {\large \wbh@autorname\par}
    \vfill
    {\small \wbh@copyrightzeile}
  \end{titlepage}%
}

% ===========================  Impressumsseite  =============================
\newcommand{\makecopyrightpage}{%
  \thispagestyle{empty}%
  \vspace*{\fill}
  \begin{center}
    \small\sffamily
    \rule{0.6\textwidth}{0.4pt}\\[1em]
    Das Studienheft und seine Teile sind urheberrechtlich geschützt.\\
    Jede Nutzung in anderen als den gesetzlich zugelassenen Fällen\\
    bedarf der vorherigen schriftlichen Zustimmung des Rechteinhabers.\\[0.5em]
    Zulässig ist das Speichern und Ausdrucken für persönliche Zwecke.\\[1em]
    \rule{0.6\textwidth}{0.4pt}
  \end{center}
  \vspace*{\fill}
  \clearpage
}

% ===========================  Vorwort  =====================================
\newcommand{\wbhvorwort}[1]{%
  \addchap{Vorwort}%
  #1%
  \clearpage
}

% ===========================  Kapiteleinleitung (kursiv)  ==================
\newcommand{\kapiteleinleitung}[1]{%
  \textit{#1}\par\medskip
}

\endinput
