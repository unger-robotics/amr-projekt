% =============================================================================
%  amr.cls
% =============================================================================
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{amr}[2025/03/04 v1.3 amr-Klasse]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{scrreprt}}
\ProcessOptions\relax

\LoadClass[
  fontsize=11.5pt,
  paper=a4,
  parskip=half,
  headings=normal,
  toc=listof,
  numbers=noenddot,
  listof=totoc,
  bibliography=totoc
]{scrreprt}

% Sprache & Schrift
\RequirePackage[ngerman]{babel}
\RequirePackage[utf8]{inputenc}
\RequirePackage[T1]{fontenc}
\RequirePackage{libertine}
\RequirePackage[libertine]{newtxmath}
\RequirePackage[scaled=0.92]{helvet}

\addtokomafont{disposition}{\sffamily\bfseries}
\addtokomafont{chapter}{\fontsize{14pt}{16.8pt}\selectfont}
\addtokomafont{section}{\fontsize{12pt}{14.4pt}\selectfont}
\addtokomafont{subsection}{\fontsize{11.5pt}{13.5pt}\selectfont}

\RequirePackage{setspace}
\setstretch{1.069}

\RequirePackage[
  left=30mm, right=25mm, top=25mm, bottom=25mm,
  headheight=15pt, headsep=12pt, footskip=20pt
]{geometry}

% Farben (AMR Theme)
\RequirePackage{xcolor}
\definecolor{amrBase}{RGB}{11,19,30}
\definecolor{amrAccent}{RGB}{0,229,255}

% Kopf- und Fußzeile (Bereinigt)
\RequirePackage{scrlayer-scrpage}
\clearpairofpagestyles
\rofoot{\footnotesize\sffamily\pagemark}
\pagestyle{scrheadings}

% Standardpakete
\RequirePackage{graphicx}
\RequirePackage{booktabs}
\RequirePackage{tabularx}
\newcolumntype{L}{>{\raggedright\arraybackslash\hspace{0pt}}X}
\RequirePackage{hyperref}
\RequirePackage{microtype}

% Titelseite (Nur Titel)
\newcommand{\maketitlepage}{%
  \begin{titlepage}
    \pagecolor{amrBase}
    \sffamily
    \noindent\textcolor{amrAccent}{\rule{\textwidth}{1pt}}

    \vspace*{0.28\textheight}

    \begin{center}
      {\color{amrAccent}\Huge\bfseries Autonomous Mobile Robot (AMR)\par}
    \end{center}

    \vfill
    \noindent\textcolor{amrAccent}{\rule{\textwidth}{1pt}}
  \end{titlepage}%
  \pagecolor{white}
  \color{black}
}

\newcommand{\abstractpage}[1]{%
  \addchap{Zusammenfassung}%
  #1\clearpage
}

\DeclareTOCStyleEntry[numwidth=3.5em]{tocline}{chapter}
\DeclareTOCStyleEntries[numwidth=4.5em]{tocline}{section,subsection}

\endinput
