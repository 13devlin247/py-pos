'''
Created on Oct 11, 2011

@author: User
'''
from xlwt import Workbook, XFStyle, Borders, Pattern, Font, Formatting

class ExcelWriter(object):
    def __init__(self, file_path):
        self.file_path = file_path
        fnt = Font()
        fnt.name = 'Arial'
        
        borders = Borders()
        borders.left = Borders.THIN
        borders.right = Borders.THIN
        borders.top = Borders.THIN
        borders.bottom = Borders.THIN
        
        pattern = Pattern()
        pattern.pattern = Pattern.SOLID_PATTERN
        pattern.pattern_fore_colour = 0xFF
        
        algn1 = Formatting.Alignment() 
        algn1.wrap = 0
        algn1.horz = Formatting.Alignment.HORZ_CENTER

        self.style = XFStyle()
        self.style.num_format_str='YYYY-MM-DD'
        self.style.font = fnt
        self.style.borders = borders
        self.style.pattern = pattern
        self.style.alignment = algn1

    def export(self, headers, contents):
        book = Workbook()
        sheet = book.add_sheet('A Date')
        for (counter, header) in enumerate(headers):
            sheet.write(0, counter, header, self.style)

        for (rows_idx, row) in enumerate(contents):
            cols = row.split(';')
            for (cols_idx, col) in enumerate(cols):
                sheet.write(rows_idx+1, cols_idx, col, self.style)

        
        book.save(self.file_path)

if __name__=="__main__":
    headers = ['Sale ID', 'Date', 'Customer', 'Cashier', 'Subtotal', 'Discount', 'Total', 'Profit']
    contents = []
    contents.append('2;Sept. 14, 2011, 5:25 p.m.;Cash 1/9/11;JESSY;920;0;920;30.88')
    contents.append('2;Sept. 14, 2011, 5:25 p.m.;Cash 1/9/11;JESSY;920;0;920;30.88')
    contents.append('2;Sept. 14, 2011, 5:25 p.m.;Cash 1/9/11;JESSY;920;0;920;30.88')
    contents.append('2;Sept. 14, 2011, 5:25 p.m.;Cash 1/9/11;JESSY;920;0;920;30.88')
    contents.append('2;Sept. 14, 2011, 5:25 p.m.;Cash 1/9/11;JESSY;920;0;920;30.88')
    contents.append('2;Sept. 14, 2011, 5:25 p.m.;Cash 1/9/11;JESSY;920;0;920;30.88')
    contents.append('2;Sept. 14, 2011, 5:25 p.m.;Cash 1/9/11;JESSY;920;0;920;30.88')
    contents.append('2;Sept. 14, 2011, 5:25 p.m.;Cash 1/9/11;JESSY;920;0;920;30.88')
    contents.append('2;Sept. 14, 2011, 5:25 p.m.;Cash 1/9/11;JESSY;920;0;920;30.88')
    contents.append('2;Sept. 14, 2011, 5:25 p.m.;Cash 1/9/11;JESSY;920;0;920;30.88')
    ExcelWriter('good.xls').export(headers, contents)
    print 'done'