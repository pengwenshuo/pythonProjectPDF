# ============================================================
# 常量：支持的文件格式
# ============================================================
IMG_FORMATS: set[str] = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif'}
WORD_FORMATS: set[str] = {'.docx', '.doc'}
EXCEL_FORMATS: set[str] = {'.xlsx', '.xls', '.xlsm'}
PPT_FORMATS: set[str] = {'.pptx', '.ppt'}

# ============================================================
# COM 常量（参考 Microsoft Office 对象模型，Office 2007+ 均稳定）
# 若将来 Office 版本变更导致常量值变化，在此处更新即可
# ============================================================
# Word: WdSaveFormat 枚举 — https://learn.microsoft.com/en-us/office/vba/api/word.wdsaveformat
WD_FORMAT_PDF: int = 17           # wdFormatPDF
WD_DO_NOT_SAVE_CHANGES: int = 0   # wdDoNotSaveChanges
# Word: Application.DisplayAlerts 属性
WD_ALERTS_NONE: int = 0           # wdAlertsNone（0=不显示任何警告对话框）
# Office: MsoAutomationSecurity 枚举 — https://learn.microsoft.com/en-us/office/vba/api/office.msoautomationsecurity
MSO_AUTOMATION_SECURITY_FORCE_DISABLE: int = 3  # msoAutomationSecurityForceDisable（禁用所有宏）
# Excel: XlFixedFormatType 枚举 — https://learn.microsoft.com/en-us/office/vba/api/excel.xlfixedformattype
XL_TYPE_PDF: int = 0              # xlTypePDF
# Excel: XlCalculation 枚举
XL_CALC_AUTOMATIC: int = -4105    # xlCalculationAutomatic
# PowerPoint: PpSaveAsFileType 枚举
PP_SAVE_AS_PDF: int = 32          # ppSaveAsPDF
# PowerPoint: PpPrintRangeType 枚举
PP_PRINT_RANGE_ALL: int = 1       # ppPrintAll
PP_PRINT_RANGE_SLIDES: int = 3    # ppPrintSlideRange
