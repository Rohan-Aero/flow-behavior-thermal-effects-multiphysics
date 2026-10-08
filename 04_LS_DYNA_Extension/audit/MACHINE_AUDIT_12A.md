# Section 12A — Machine Audit for LS-DYNA (evidence record)

> **Method.** Read-only, on device `HOST` (Windows 11 Home Single Language 10.0.26200), 2026-10-02, using PowerShell
> through Desktop Commander. No ANSYS or LS-DYNA software was installed, launched or configured, and no project file was
> changed.
>
> **Re-run.** `machine_audit_12A.ps1` reproduces checks 1–8 and writes `machine_audit_12A_output.txt`; the run of
> 2026-10-02 13:10 is kept. The full-drive searches are in `raw/`.
>
> One helper was installed to read the LS-DYNA manuals as text: the `pypdf` package, into
> `%TEMP%\claude_pypdf` (outside the project). No Python environment was changed.

## 1. LS-DYNA solver, LS-PrePost, LS-Run

| Search | Scope | Result |
|---|---|---|
| `lsdyna*`, `ls-dyna*`, `lsprepost*`, `ls-prepost*`, `lspp*`, `mppdyna*`, `smpdyna*` (any extension) | `C:\Program Files\ANSYS Inc`, recursive | Only integration DLLs, Python plug-ins, XML, docs and VTK readers (`raw/ansys_tree_lsdyna_named_files_2026-10-02.txt`). **No solver, LS-PrePost or LS-Run executable** |
| `dir /s` for `*lsdyna*.exe *ls-dyna*.exe *lsprepost*.exe *lsrun*.exe *mppdyna*.exe *smpdyna*.exe` | all of `C:\` | `File Not Found` (`raw/exe_search_C_drive_2026-10-02.txt`) |
| same, plus `*.k` | all of `D:\` | `File Not Found` (`raw/exe_and_k_search_D_drive_2026-10-02.txt`) |
| Expected LS-PrePost location | `ansys\bin\winx64\lsprepost413\lsprepost4.13.exe`, from `installer\dev_configs\lsdyna\config_lsdyna.json` | Path does not exist. `ansys\bin\winx64` (165 files) holds no dyna, LS-PrePost or LS-Run file |
| Start-menu folders named LS-DYNA, PrePost or LS-Run | ProgramData and AppData Start menus | None. The Ansys 2026 R1 Start-menu group has no LS-DYNA entry |
| Registry uninstall entries | HKLM / HKCU | The query returned no matching entry. Ansys Student itself was not listed either, so this check is **weak** and is not used as evidence |
| Installers in `Downloads` named dyna, prepost or lstc | depth 1 | None. The Ansys Student installation media is no longer in Downloads |

**Solver version:** not obtainable, because there is no executable. The installed manuals are *LS-DYNA Keyword User's
Manual R16@431ab7b9b (10/29/25)*, Vol I (4,194 pages), II (2,174 pages) and III. They document the R16 keyword set that
the 2026 R1 integration targets; they are not a solver.

## 2. What the Ansys Student installation contains

- **Product.** Ansys Student 2026 R1, `C:\Program Files\ANSYS Inc\ANSYS Student\v261`. Package `R261RC2P01`, created
  202602040408P01.
- **Installation.** 2026-09-17 21:24–21:48, from `Downloads\ANSYSACADEMICSTUDENT_2026R1_WINX64`.
- **Product selection** (`install.log` header): the Structures group contains **Aqwa, Autodyn, Material Calibration App,
  Mechanical Products, Motion. LS-DYNA is not listed**, and no `lsdyna` media package appears in the extraction list.
- **Install warnings.** The installation "completed with warnings/errors". `install.err` shows extraction failures for
  `python_site_syscplg` and `tp\cudss`, unrelated to LS-DYNA.
- **`C:\Program Files\ANSYS Inc\v261`** (not the Student tree) holds only `installer\`, `builddate.txt`, `install.id` and
  `package.id`. Its timestamps (`install.id` 202610012154) match the License Manager installation of 2026-10-01, and it
  contains no product.

## 3. LS-DYNA integration components present (they cannot solve)

| Component | Path (under `v261`) |
|---|---|
| Workbench LS-DYNA ACT extension | `Addins\ACT\extensions\LSDYNA.wbex` (2,103,016 B), `LSDYNA\LSDynaSolverExtension.dll`, `LSDYNAAnalysisTemplate.xml`, `RestartLSDYNAAnalysisTemplate.xml`, `LSDYNAAcousticAnalysisTemplate.xml`, `LSDYNASolverRepresentation.xml` |
| Keyword manager | `Addins\ACT\extensions\keywordmanager\Ansys.ACTLSDYNA.KeywordLibrary.dll`, `…KeywordParser.dll` |
| Mechanical plug-ins | `aisol\bin\winx64\Ans.Addins.LSDYNASolverCOM.dll`, `LSDYNAParser.dll`, `Ans.Post.ResultReaderPlugInLSDYNACOM.dll`, `Ansys.SolverManager.Proxies.(WB)LSDYNA.dll` |
| Solver launch hooks | `SEC\SolverExecutionController\sec\plugins\lsdyna.py`; `commonfiles\launcherQT\src\RunLsdyna.py`, `LsdynaTabs.py`; `RSM\Config\xml\Mechanical_LSDYNAJob.xml`; `SystemCoupling\Participants\LsDyna\*.bat` |
| Engineering Data LS-DYNA material metadata | `Addins\EngineeringData\Metadata\LSDYNA_*.xml`, `ACTLSDYNA_*.xml` |
| Manuals | `ansys\docu\LS-DYNA_Manual_Vol_I/II/III_R16.pdf` |
| Sample keyword decks | `tp\MPI\WindowsHPC\mat_pie_lin_pla.k` (with `runlsdyna.bat`, an MPI test); `optiSLang\examples\simple_car\reference\simplecar.k`. A `.k` file also exists in EnSight sample data (`CEI\ensight261\data\racecar\`); it was not inspected |

- **Loaded by default.** The ACT default-extension list (`%APPDATA%\Ansys\v261\UserRegFiles_*\ACTPreferences.xml`) contains
  `LSDYNA … 2026`.
- **Loaded in the project.** The project's Mechanical decks record `/COM, LSDYNA, 2026.1` among the loaded extensions.
- **So:** the Workbench Toolbox should offer an "LS-DYNA" analysis system. This was **not opened or tested** in 12A.
  Without the solver executable it can prepare a model and write keyword input, but it cannot solve.

## 4. Licensing evidence

| Item | Value |
|---|---|
| `LSTC_LICENSE` (machine) | `Ansys`. This tells an LS-DYNA executable to use Ansys licensing. Who set it is not determined |
| `ANSYSLMD_LICENSE_FILE`, `LSTC_LICENSE_SERVER`, `LSTC_FILE` | not set |
| `ANSYSLIC_DIR` (machine) | `C:\Program Files\ANSYS Inc\Shared Files\Licensing`, set 2026-10-01 by the License Manager configuration |
| `AWP_ROOT261`, `ANSYS261_DIR` (machine) | Student `v261` tree |
| Licence files | `Shared Files\Licensing\license_files\` contains only an empty `backup\` folder. No `ansyslmd.ini` |
| Services | `ANSYS, Inc. License Manager CVD`: **Stopped**, Automatic. `ANSYS Licensing Tomcat`: Running, Automatic |
| License Manager installation | 2026-10-01 21:54–21:55, `instcore.exe -Silent -LM` launched from `Downloads\Ansys_STK_Pro_ODTK_v13.1.0\Ansys License Manager`. Its configuration log ends: *"No license files were found."* |
| Ansys Student | uses its own built-in or account licensing (`00_admin/software_inventory.md` §2) |

**Interpretation.**

- There is no LS-DYNA licence on the machine, and no LS-DYNA product that could use one.
- The License Manager came from another product's media. It holds no licence file and plays no part in this project.
- Ansys LS-DYNA Student would bring its own built-in licence (vendor page).
- Whether the existing `LSTC_LICENSE=Ansys` helps or interferes with it is checked in gate G0.

## 5. Hardware

| Item | Value |
|---|---|
| CPU | Intel Core i5-12450HX, 8 cores / 12 logical processors |
| RAM | 15.71 GB (2 × 8 GB DDR5-5600). Free at audit: 4.2–5.0 GB |
| GPU | NVIDIA GeForce RTX 3050 6 GB Laptop; Intel UHD (not used by implicit LS-DYNA) |
| Disk | C: 107 GB free; D: 199 GB free |

**Reference load on this machine.** The same mesh in MAPDL (`LC2_Restrained/Solver_Output/solve.out`):

- 323,529 equations;
- in-core solver memory 4.3 GB;
- 5,205 MB used in total over 4 distributed processes;
- 51.2 s elapsed.

The LC2 linear buckling run took 255.0 s.

## 6. Ansys LS-DYNA Student: published limits (external, unverified here)

From [ansys.synopsys.com/academic/students/ansys-ls-dyna-student](https://ansys.synopsys.com/academic/students/ansys-ls-dyna-student),
read 2026-10-02:

- separate download (`.msi`; reboot after install);
- **"128K nodes/elements"**;
- includes LS-PrePost and LS-Run;
- "Renewable, twelve-month lease"; built-in licence "valid until 7/31/27";
- educational use only ("self-learning, student instruction, student projects, and student demonstrations");
- Windows 10 64-bit, at least 4 GB RAM.

The page **does not state** whether implicit analysis is supported.

Implicit LS-DYNA needs a double-precision (`_dp`) executable:

- the Ansys Innovation Space thread on error 60022 states *"LS-DYNA Implicit is not supported in single precision"*;
- manual Vol I, `*CONTROL_IMPLICIT_BUCKLE` remark 5 recommends a double-precision executable for buckling.

## 7. Mechanical export / keyword workflow

- **Workbench LS-DYNA system.** Present and loaded, but untested. Not required: the LC2 MAPDL deck holds the complete
  model.
- **Keyword files in the project:** none (`*.k`, `*.key`, `*.dyn`, `d3plot*`, `d3eigv*`, `binout*`). **No keyword
  workflow exists.**
