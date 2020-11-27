#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Serge"

from decimal import Decimal, InvalidOperation
from bs4 import BeautifulSoup
import xlsxwriter
import cssutils
import sys
from PyQt5 import QtGui, QtWidgets
import os
import random

"""
Parsing html with BeautifulSoup and cssutils and writing xlsx with xlsxwriter
"""


def is_html(f_path):
    """Check if it's already xlsx"""

    # check file extension
    ext = f_path.split(".")[-1]

    if ext == "xlsx" or ext == "xls":
        return False  # Nothing to transform
    else:
        return True


def get_number(s):
    """get number from string i.e. 12px => 12"""
    result = ""
    for c in s:
        if c.isdigit() or c == ".":
            result += c
    return float(result)


def xl_width(style):
    """Get size from style in pixels and transform it to excel width"""
    s = cssutils.parseStyle(style)
    width = s["width"]
    if width != "":
        px = get_number(width)
    else:
        px = 0
    return (px / 7.15)  # something like that... I mean Calibri 11 is 7px width


def xl_height(style):
    """Get size from style in pixels and transform it to excel height"""
    s = cssutils.parseStyle(style)
    height = s["height"]
    if height != "":
        px = get_number(height)
    else:
        px = 0
    return (px * 0.7)


def check_coordinates(merged, xl_row, xl_col):
    """Check if coordinates crossed already merged cells"""
    for merge in merged:
        row_start = merge[0]
        col_start = merge[1]
        row_end = merge[2]
        col_end = merge[3]

        if row_start <= xl_row <= row_end:  # if we hit merged row
            if col_start <= xl_col <= col_end:  # if we hit column
                xl_col = col_end + 1  # then reposition next to it's end
                return check_coordinates(merged, xl_row, xl_col)
    return xl_row, xl_col


def transform(f_path, progress=None, need_password=False):
    """Parse HTML and write XLSX"""
    mode = (True if progress else False, True if need_password else False)
    c = 0

    if not is_html(f_path):
        return f_path

    # We need to change file extension to xlsx
    f_xlsx = f_path.split(".")
    f_xlsx[-1] = "xlsx"
    f_xlsx = ".".join(f_xlsx)

    # starting excel file
    workbook = xlsxwriter.Workbook(f_xlsx)

    # Create object for parsing
    with open(f_path, "r", encoding="utf-8") as html:
        soup = BeautifulSoup(html, "html.parser")

    if mode[0]:
        v = 20  # will be used in row iteration
        progress.setValue(v)

    tables = soup.findChildren("table")

    for table in tables:
        # Get worksheet settings from <table> attributes
        attrs = table.attrs
        try:
            name = attrs["name"]
        except KeyError:
            name = ""

        worksheet = workbook.add_worksheet(name)
        # Default worksheet settings
        worksheet.set_landscape()
        worksheet.outline_settings(True)

        if need_password:
            symbols = '123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'
            password = ''.join([random.choice(list(symbols)) for x in range(12)])

            worksheet.protect(password)

        xl_row = 0
        xl_col = 0
        merged = []  # list of merged cells i.e. [(1,1,3,3)] - square 3x3

        for attr in table.attrs:
            if attr == "hide_zero":
                if attrs["hide_zero"].lower() == "true":
                    worksheet.hide_zero()

            elif attr == "repeat_rows":
                try:
                    r_rows = attrs["repeat_rows"].split(":")
                    worksheet.repeat_rows(int(r_rows[0])-1, int(r_rows[1])-1)
                except (KeyError, TypeError):
                    pass

            elif attr == "orientation":
                orient = attrs["orientation"].lower()
                if orient == "landscape":
                    worksheet.set_landscape()
                elif orient == "portrait":
                    worksheet.set_portrait()

            elif attr == "fit_to_page":
                if attrs["fit_to_page"].lower() == "true":
                    worksheet.fit_to_pages(1, 0)

            elif attr == "outline_below":
                if attrs["outline_below"].lower() == "false":
                    worksheet.outline_settings(True, False, True, False)

        rows = table.findChildren("tr")

        if mode[0]:
            #  For progress bar
            p = round((len(rows)/80)*len(tables))
            if p == 0:
                p = 1  # Prevent zero division
            i = 0

        column_width = []
        row_height = []

        # Now we will go through all tr
        for row in rows:
            xl_col = 0
            if "class" in row.attrs and "set_columns" in row["class"]:
                # Lets set columns widths
                xl_col = 0

                columns = row.findChildren("td")

                for col in columns:
                    try:
                        width = xl_width(col["style"])
                        column_width.append(width)
                        if width != 0:
                            worksheet.set_column(xl_col, xl_col, width)
                    except KeyError:
                        pass
                    xl_col += 1
                continue  # skip to next row
            elif not column_width:
                columns = row.findChildren("td")

                default_width = 8.43
                for col in columns:
                    column_width.append(default_width)
            # Get row settings from <tr> attributes

            # check for height
            try:
                height = xl_height(row["style"])
                if height == 0:
                    height = 15  # default value
            except KeyError:
                height = 15

            attrs = row.attrs
            options = {}
            for attr in attrs:
                if attr == "level":
                    options = {"level": int(attrs["level"])-1}

            worksheet.set_row(xl_row, height, None, options)
            row_height.append(height)

            cells = row.findChildren(["td", "th"])
            for cell in cells:
                img_align = "left"
                xl_row, xl_col = check_coordinates(merged, xl_row, xl_col)

                # real value
                try:
                    xl_val = cell["val"]  # real value
                except KeyError:
                    xl_val = cell.text  # value for html

                # formats

                cell_format = workbook.add_format()

                attrs = cell.attrs
                for attr in attrs:
                    if attr == "num":
                        try:
                            xl_val = xl_val.replace(",", ".")
                            xl_val = Decimal(xl_val)
                        except InvalidOperation:
                            pass
                        num_format = attrs["num"]
                        if num_format == "":
                            cell_format.set_num_format(0)
                        else:
                            cell_format.set_num_format(num_format)

                # Apply default formats
                parent = cell.parent.parent.name
                if parent == "tbody":
                    cell_format.set_border(1)

                if cell.name == "th":
                    cell_format.set_bold()
                    cell_format.set_align("center")
                    cell_format.set_align("vcenter")
                    cell_format.set_text_wrap()

                # parse styles
                try:
                    style = cssutils.parseStyle(cell["style"])

                    for s in style:
                        key = s.name.lower()
                        val = s.value.lower()

                        if key == "text-align":
                            if val in ["left", "right", "center"]:
                                cell_format.set_align(val)
                                if val != "center":
                                    img_align = val

                        elif key == "vertical-align":
                            if val in ["top", "middle", "bottom"]:
                                if val == "middle":
                                    val = "vcenter"
                                cell_format.set_align(val)

                        elif key == "font-style" and val == "italic":
                            cell_format.set_italic()

                        elif key == "font-weight" and val == "bold":
                            cell_format.set_bold()

                        elif key == "border":
                            if val == "1px solid black":
                                cell_format.set_border()
                            elif val == "0":
                                cell_format.set_border(0)

                        elif key == "border-bottom":
                            if val == "1px solid black":
                                cell_format.set_bottom()
                            elif val == "0":
                                cell_format.set_bottom(0)

                        elif key == "border-top":
                            if val == "1px solid black":
                                cell_format.set_top()
                            elif val == "0":
                                cell_format.set_top(0)

                        elif key == "border-left":
                            if val == "1px solid black":
                                cell_format.set_left()
                            elif val == "0":
                                cell_format.set_left(0)

                        elif key == "border-right":
                            if val == "1px solid black":
                                cell_format.set_right()
                            elif val == "0":
                                cell_format.set_right(0)

                        elif key == "background-color":
                            try:
                                cell_format.set_bg_color(val)
                            except TypeError:
                                pass

                        elif key == "color":
                            try:
                                cell_format.set_font_color(val)
                            except TypeError:
                                pass

                        elif key == "font-family":
                            try:
                                cell_format.set_font_name(val)
                            except TypeError:
                                pass

                        elif key == "font-size":
                            try:
                                cell_format.set_font_size(get_number(val))
                            except TypeError:
                                pass

                        elif key == "text-decoration":
                            if val == "underline":
                                cell_format.set_underline()
                            elif val == "line-through":
                                cell_format.font_strikeout()

                except KeyError:
                    pass

                try:
                    text_wrap = cell["text_wrap"].lower()
                    if text_wrap == "true":
                        cell_format.set_text_wrap(True)
                    elif text_wrap == "false":
                        cell_format.set_text_wrap(False)
                except (KeyError, TypeError):
                    pass

                # merging
                try:
                    colspan = int(cell["colspan"]) - 1
                except KeyError:
                    colspan = 0
                try:
                    rowspan = int(cell["rowspan"]) - 1
                except KeyError:
                    rowspan = 0

                if colspan != 0 or rowspan != 0:
                    worksheet.merge_range(xl_row, xl_col, xl_row + rowspan, xl_col + colspan, xl_val, cell_format)
                    merged.append((xl_row, xl_col, xl_row + rowspan, xl_col + colspan))  # add merged cells to list
                else:
                    worksheet.write(xl_row, xl_col, xl_val, cell_format)

                images = cell.findChildren('img')
                try:
                    if images:
                        sum_offset = 0
                        max_height = 0
                        sum_width = 0
                        cell_width_px = sum(column_width[xl_col:xl_col + colspan + 1]) * 11.93
                        if img_align == "right":
                            images = images[::-1]
                        for img in images:
                            if os.path.basename(img.attrs['src']) == img.attrs['src']:
                                img_name = os.path.dirname(os.path.realpath(f_path)) + os.sep + os.path.basename(
                                    img.attrs['src'])
                            else:
                                img_name = img.attrs['src']
                            if not os.path.exists(img_name):
                                continue
                            image = QtGui.QImage()
                            image.load(img_name)
                            real_width_px, real_height_px = image.size().height(), image.size().width()
                            img_width_px = img_height_px = None
                            x_scale = y_scale = 1
                            try:
                                img_width_px = float(img['width'])
                                x_scale = img_width_px / real_width_px
                            except (ValueError, KeyError):
                                pass
                            except ZeroDivisionError:
                                continue

                            try:
                                img_height_px = float(img['height'])
                                y_scale = img_height_px / real_height_px
                            except (ValueError, KeyError):
                                pass
                            except ZeroDivisionError:
                                continue

                            if img_width_px is None:
                                if img_height_px is None:
                                    img_width_px = real_width_px
                                    img_height_px = real_height_px
                                else:
                                    x_scale = y_scale
                                    img_width_px = real_width_px * x_scale
                            elif img_height_px is None:
                                    y_scale = x_scale
                                    img_height_px = real_height_px * y_scale

                            sum_width += img_width_px
                            if img_height_px > max_height:
                                max_height = img_height_px
                            x_offset = 0
                            y_offset = 0
                            if img_align == "left":
                                x_offset += sum_offset
                            elif img_align == "right":
                                x_offset = cell_width_px - sum_offset - img_width_px

                            worksheet.insert_image(xl_row, xl_col, img_name, {'x_offset': x_offset,
                                                                              'y_offset': y_offset,
                                                                              'x_scale': x_scale,
                                                                              'y_scale': y_scale})
                            sum_offset += img_width_px
                        if sum_width > cell_width_px:
                            worksheet.set_column(xl_col, xl_col, ((sum_width - cell_width_px) / 11.93 + column_width[xl_col]) * 1.7)
                        cell_height_px = (row_height[xl_row] + rowspan * 15) / 0.7
                        if max_height > cell_height_px:
                            worksheet.set_row(xl_row, (max_height - cell_height_px) * 0.8 + row_height[xl_row], None, options)
                except KeyError:
                    pass
                xl_col += 1

            if mode[0]:
                # Progress bar
                i += 1
                if i % p == 0:
                    v += 1
                    progress.setValue(v)

            xl_row += 1

    # close excel

    status = True

    try:
        workbook.close()
    except xlsxwriter.exceptions.FileCreateError:
        msg = QtWidgets.QMessageBox()
        ico_path = os.path.dirname(os.path.realpath(sys.argv[0])) + os.sep + "rep.png"
        msg.setWindowIcon(QtGui.QIcon(ico_path))
        msg.setWindowTitle("Внимание")
        msg.setText(f"Файл {f_xlsx} занят другой программой")
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.exec_()
        status = False
    return f_xlsx, status
