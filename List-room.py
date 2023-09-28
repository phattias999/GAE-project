from flask import Flask, request, render_template, redirect, session, url_for
from google.cloud import storage
import mysql.connector
import datetime as dt
from firebase_admin import credentials
import pycountry
import re

app = Flask(__name__)
# Đặt key bí mật cho phiên làm việc (session)
app.secret_key = "admin"
# Dùng đề config với firebase


# kiểm tra xem thông tin đăng nhập của manager
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="cnpm",
        )
        mycursor = mydb.cursor()
        query = f"SELECT Namelogin, passwordlogin FROM adminmanager WHERE Namelogin = '{email}' AND passwordlogin = '{password}'"
        mycursor.execute(query)
        myresult = mycursor.fetchone()

        if myresult:
            session["email"] = email
            return redirect(
                url_for("Room")
            )  # Điều hướng đến trang Room khi đăng nhập thành công

    return render_template("login.html")


@app.route("/login.html")
def logout():
    session.pop("email", None)
    return redirect(url_for("login"))  # Điều hướng đến trang đăng nhập


# Điều hướng trang phòng
@app.route("/widgets.html")
def Room():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        Sqlquery = "SELECT 	MAPHONG,TenPhong,LoaiPhong,DonGia,TinhTrang,GhiChu,	Imagephong FROM phong"
        mycursor.execute(Sqlquery)
        result = mycursor.fetchall()
        mycursor.close()
        mydb.close()
        return render_template(
            "widgets.html", data=result
        )  # Thêm "return" ở đây để hiển thị template

    else:
        return redirect(
            "login"
        )  # Điều hướng đến trang login nếu email không tồn tại trong session


# Điều hướng đến trang thêm phòng
@app.route("/add_infor_room", methods=["GET", "POST"])
def add_infor_room():
    message = ""  # Khởi tạo biến thông báo rỗng
    # Kiểm tra nếu người dùng đã đăng nhập bằng session
    if "email" in session:
        if request.method == "POST":
            MAPHONG = request.form["MAPHONG"]
            TENPHONG = request.form["TENPHONG"]
            LOAIPHONG = request.form["LOAIPHONG"]
            DONGIA = request.form["DONGIA"]
            TINHTRANG = request.form["TINHTRANG"]
            GHICHU = request.form["GHICHU"]

            file = request.files["IMAGEPHONG"]  # Sửa key này thành "IMAGEPHONG"
            if file:
                bucket_name = "image-899c9.appspot.com"  # Tên bucket name trên Firebase
                storage_client = storage.Client.from_service_account_json(
                    "E:/path/to/your/serviceAccountKey.json"
                )
                bucket = storage_client.get_bucket(bucket_name)
                blob = bucket.blob("images/" + file.filename)
                blob.upload_from_file(file)
                image_url = blob.public_url

                # Kết nối CSDL và thêm dữ liệu
                mydb = mysql.connector.connect(
                    host="localhost", user="root", password="", database="cnpm"
                )
                mycursor = mydb.cursor()

                # Kiểm tra sự tồn tại của phòng
                sqlcheck = "SELECT MAPHONG FROM phong WHERE MAPHONG=%s"
                val = MAPHONG
                mycursor.execute(sqlcheck, val)
                existing_room = mycursor.fetchone()

                if existing_room:
                    message = "Mã phòng đã tồn tại!"  # Đặt thông báo tồn tại mã phòng
                else:
                    sql = "INSERT INTO phong (MAPHONG, TenPhong, LoaiPhong, DonGia, TinhTrang, GhiChu, Imagephong) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    val = (
                        MAPHONG,
                        TENPHONG,
                        LOAIPHONG,
                        DONGIA,
                        TINHTRANG,
                        GHICHU,
                        image_url,
                    )
                    mycursor.execute(sql, val)
                    mydb.commit()  # Commit thay đổi vào cơ sở dữ liệu
                    message = (
                        "Thêm thông tin phòng thành công!"  # Đặt thông báo thành công
                    )
                    return render_template("add_infor_room.html", message=message)
                return render_template("add_infor_room.html", message=message)
        return render_template("add_infor_room.html", message=message)
    return redirect("login")


# Điều hướng đến trang xem chi tiết phòng
@app.route("/show_infor_room/<item_id>", methods=["GET"])
def show_infor_room(item_id):
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sqlshow = "SELECT * FROM phong WHERE MAPHONG=%s"
        val = (item_id,)
        mycursor.execute(sqlshow, val)
        show_room = mycursor.fetchone()
        return render_template("show_infor_room.html", data_show_room=show_room)
    else:
        return redirect("login")


# Điều hướng đến trang chỉnh sửa phòng
@app.route("/edit_infor_room/<item_id>", methods=["GET", "POST"])
def edit_infor_room(item_id):
    message = ""  # Khởi tạo biến thông báo rỗng
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sqlshow = "SELECT * FROM phong WHERE MAPHONG=%s"
        val = (item_id,)
        mycursor.execute(sqlshow, val)
        edit_room = mycursor.fetchone()
        if request.method == "POST":
            MAPHONG = request.form["MAPHONG"]
            TENPHONG = request.form["TENPHONG"]
            LOAIPHONG = request.form["LOAIPHONG"]
            DONGIA = request.form["DONGIA"]
            TINHTRANG = request.form["TINHTRANG"]
            GHICHU = request.form["GHICHU"]
            sql = "UPDATE phong SET MAPHONG =%s,TenPhong=%s,LoaiPhong=%s,DonGia=%s,TinhTrang=%s, GhiChu=%s WHERE MAPHONG = %s"
            val = (MAPHONG, TENPHONG, LOAIPHONG, DONGIA, TINHTRANG, GHICHU, item_id)
            try:
                mycursor.execute(sql, val)
                mydb.commit()
                message = "Cập nhật thông tin thành công!"
            except Exception as e:
                message = "Cập nhật thông tin không thành công!"
        return render_template(
            "edit_infor_room.html",
            item_id=item_id,
            data_edit_room=edit_room,
            message=message,
        )
    else:
        return redirect("login")


# Điều hướng xóa phòng
@app.route("/delete_room/<item_id>")
def delete_infor_room(item_id):
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "DELETE FROM phong WHERE MAPHONG = %s"
        val = (item_id,)  # Đảm bảo val là một tuple chứa giá trị item_id
        mycursor.execute(sql, val)
        mydb.commit()
        # Sau khi xóa phòng, bạn có thể chuyển hướng người dùng đến trang danh sách phòng hoặc bất kỳ trang nào bạn muốn.
        return redirect("Room")
    else:
        return redirect("login")


# Điều hướng đến trang Gia hạn ngày thuê
@app.route("/general_elements.html")
def general_elements():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM giahanngaythue"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("general_elements.html", data=result)
    else:
        return redirect("login")


# Điều hướng đến trang chỉnh sửa gia hạn phòng
@app.route("/edit_retal_date/<item_id>", methods=["GET", "POST"])
def edit_retal_date(item_id):
    message = ""  # Khởi tạo biến thông báo rỗng
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql_show_retal_date = "SELECT * FROM giahanngaythue WHERE  MAGH=%s"  # câu lệnh truy vấn để hiên thị thông tin
        val_show_retal_date = (item_id,)  # Gán giá trị cho câu lệnh where để truy vấn
        mycursor.execute(sql_show_retal_date, val_show_retal_date)
        result_show_retal_date = mycursor.fetchone()
        if request.method == "POST":
            MAGH = request.form["MAGH"]
            NgayThuehientai = request.form["NgayThuehientai"]
            NgayThuemoi = request.form["NgayThueMoi"]
            ngay_thue_hien_tai = dt.datetime.strptime(
                NgayThuehientai, "%Y-%m-%d"
            )  # strftime dùng để chuyền ngày qua kiểu y-m-d
            ngay_thue_moi = dt.datetime.strptime(
                NgayThuemoi, "%Y-%m-%d"
            )  # strftime dùng để chuyền ngày qua kiểu y-m-d
            ngay_thue_phong_tuong_lai = ngay_thue_hien_tai + dt.timedelta(
                days=90
            )  # strftime dùng để chuyền ngày qua kiểu y-m-d
            if ngay_thue_moi < ngay_thue_hien_tai:
                message = "vui lòng nhập ngày thuê lớn hơn ngày hiện tại"
                return render_template(
                    "edit_retal_date.html",
                    item_id=item_id,
                    message=message,
                    data_edit_retal_date=result_show_retal_date,
                )
            elif ngay_thue_moi > ngay_thue_phong_tuong_lai:
                message = "vui lòng nhập ngày thuê mới"
                return render_template(
                    "edit_retal_date.html",
                    item_id=item_id,
                    message=message,
                    data_edit_retal_date=result_show_retal_date,
                )
            elif ngay_thue_moi == ngay_thue_hien_tai:
                message = "vui lòng nhập ngày thuê mới lớn hơn ngày thuê hiện tại"
                return render_template(
                    "edit_retal_date.html",
                    item_id=item_id,
                    message=message,
                    data_edit_retal_date=result_show_retal_date,
                )
            else:
                sql_retal_date = (
                    "UPDATE giahanngaythue SET NgayThueMoi=%s WHERE MAGH=%s"
                )
                val = (NgayThuemoi, item_id)
                try:  # kiểm tra xem nó có truy ván thành công không?.
                    mycursor.execute(sql_retal_date, val)
                    mydb.commit()
                    message = "Cập nhật thành công!"
                except Exception as e:
                    message = "Cập nhật không thành công!"
                return render_template(  # reload lại trang nếu truy vấn thành công
                    "edit_retal_date.html",
                    item_id=item_id,
                    data_edit_retal_date=result_show_retal_date,
                    message=message,
                )
        return render_template(
            "edit_retal_date.html",
            item_id=item_id,
            message=message,
            data_edit_retal_date=result_show_retal_date,
        )
    else:
        return redirect("login")


# Điều hướng xóa gia hạn phòng
@app.route("/delete_retaldate/<item_id>")
def delete_retal_date(item_id):
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "DELETE FROM giahanngaythue WHERE MAGH = %s"
        val = (item_id,)  # Đảm bảo val là một tuple chứa giá trị item_id
        mycursor.execute(sql, val)
        mydb.commit()
        # Sau khi xóa phòng, bạn có thể chuyển hướng người dùng đến trang danh sách phòng hoặc bất kỳ trang nào bạn muốn.
        return redirect("general_elements")
    else:
        return redirect("login")


# Điều hướng tình trạng phòng
@app.route("/media_gallery.html")
def media_gallery():
    return render_template("media_gallery.html")


# Điều hướng hủy phòng
@app.route("/icons.html")
def icons():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM huythuephong"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("icons.html", data=result)
    else:
        return redirect("login")


# Điều hướng đến trang chỉnh sửa hủy thuê phòng
@app.route("/edit_destroy_room/<item_id>", methods=["GET", "POST"])
def edit_destroy_room(item_id):
    message = ""  # Khởi tạo biến thông báo rỗng
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql_show_destroy = "SELECT * FROM huythuephong WHERE MAPTPHUY=%s "
        val_show_destroy = (item_id,)
        mycursor.execute(sql_show_destroy, val_show_destroy)
        result_show_destroy = mycursor.fetchone()
        if request.method == "POST":
            MAPTPHUY = request.form["MAPTPHUY"]
            LyDoHuy = request.form["LyDoHuy"]
            if not LyDoHuy:
                message = "Không được để rỗng"
                return render_template(
                    "edit_destroy_room.html",
                    item_id=item_id,
                    destroy_room=result_show_destroy,
                    message=message,
                )
            else:
                sql_update_destroy_room = (
                    "UPDATE huythuephong SET LyDoHuy=%s WHERE MAPTPHUY=%s"
                )
                val_update_destroy_room = (LyDoHuy, item_id)
                try:
                    mycursor.execute(sql_update_destroy_room, val_update_destroy_room)
                    mydb.commit()
                    message = "Cập nhật thành công"
                except Exception as e:
                    message = "Cập nhật không thành công"
                return render_template(
                    "edit_destroy_room.html",
                    item_id=item_id,
                    destroy_room=result_show_destroy,
                    message=message,
                )
        return render_template(
            "edit_destroy_room.html", item_id=item_id, destroy_room=result_show_destroy
        )
    else:
        return redirect("login")


# Điều hướng xóa hủy thuê phòng
@app.route("/delete_destroy_room/<item_id>")
def delete_destroy_room(item_id):
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "DELETE FROM huythuephong WHERE MAGH = %s"
        val = (item_id,)  # Đảm bảo val là một tuple chứa giá trị item_id
        mycursor.execute(sql, val)
        mydb.commit()
        # Sau khi xóa phòng, bạn có thể chuyển hướng người dùng đến trang danh sách phòng hoặc bất kỳ trang nào bạn muốn.
        return redirect("icons")
    else:
        return redirect("login")


# Điều hướng thay đổi phòng
@app.route("/invoice.html")
def invoice():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM thaydoiphong"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("invoice.html", data=result)
    else:
        return redirect("login")


# Điều hướng đến chỉnh sửa thay đổi phòng
@app.route("/edit_change_room/<item_id>", methods=["POST", "GET"])
def edit_change_room(item_id):
    message = ""  # Khởi tạo biến thông báo rỗng
    # Kiểm tra nếu người dùng đã đăng nhập bằng session
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        # Get information from thaydoiphong
        sql_show_change_room = "SELECT * FROM thaydoiphong WHERE MaPTP=%s"
        val_show_change_room = (item_id,)
        mycursor.execute(sql_show_change_room, val_show_change_room)
        result_change_room = mycursor.fetchone()
        # check method ==post
        if request.method == "POST":
            MaPTP = request.form["MaPTP"]
            NgayThucHien = request.form["NgayThucHien"]
            LoaiPhongBanDau = request.form["LoaiPhongBanDau"]
            LoaiPhongMoi = request.form["LoaiPhongMoi"]
            TongChiPhiThayDoi = request.form["TongChiPhiThayDoi"]
            Ngay_thuc_hien = dt.datetime.strftime(
                NgayThucHien, "%Y-%m-%d"
            )  # strftime dùng để chuyền ngày qua kiểu y-m-d
            # Get information from phieuthuephong
            sql_get_phieuthuephong = "SELECT * FROM phieuthuephong WHERE MAPTP=%s"
            val_get_phieuthuephong = (item_id,)
            mycursor.execute(sql_get_phieuthuephong, val_get_phieuthuephong)
            result_get_phieuthuephong = mycursor.fetchone()
            NgayTraPhong = result_get_phieuthuephong["NgayTraPhong"]
            Ngay_tra_phong = dt.datetime.strftime(
                NgayTraPhong, "%Y-%m-%d"
            )  # strftime dùng để chuyền ngày qua kiểu y-m-d
            Ngay_thue_phong_tuong_lai = dt.timedelta(
                days=90
            )  # strftime dùng để chuyền ngày qua kiểu y-m-d
            if Ngay_thuc_hien < Ngay_tra_phong:
                message = "Ngày thay đổi phải lớn hơn ngày trả phòng"
                return render_template(
                    "edit_change_room.html",
                    item_id=item_id,
                    data_change_room=result_change_room,
                    message=message,
                )
            elif Ngay_thuc_hien > Ngay_thue_phong_tuong_lai:
                message = "Ngày thay đổi phải nhỏ hơn 90 ngày"
                return render_template(
                    "edit_change_room.html",
                    item_id=item_id,
                    data_change_room=result_change_room,
                    message=message,
                )
            else:
                sql_change_room = (
                    "UPDATE thaydoiphong SET LoaiPhongMoi=%s WHERE MaPTP=%s"
                )
                val_change_room = (LoaiPhongMoi, item_id)
                try:
                    mycursor.execute(sql_change_room, val_change_room)
                    mydb.commit()
                    message = "Cập nhật thành công"
                except Exception as e:
                    message = "Cập nhật không thành công"
                return render_template(
                    "edit_change_room.html",
                    item_id=item_id,
                    data_change_room=result_change_room,
                    message=message,
                )
        return render_template(
            "edit_change_room.html",
            item_id=item_id,
            data_change_room=result_change_room,
            message=message,
        )
    else:
        return redirect("login")


# Điều hướng xóa thay đổi phòng
@app.route("/data_change_room/<item_id>")
def data_change_room(item_id):
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "DELETE FROM thaydoiphong WHERE MaPTP = %s"
        val = (item_id,)  # Đảm bảo val là một tuple chứa giá trị item_id
        mycursor.execute(sql, val)
        mydb.commit()
        # Sau khi xóa phòng, bạn có thể chuyển hướng người dùng đến trang danh sách phòng hoặc bất kỳ trang nào bạn muốn.
        return redirect("invoice")
    else:
        return redirect("login")


# Điều hướng trang khách hàng
@app.route("/tables.html")
def tables():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM khachhang"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("tables.html", data=result)
    else:
        return redirect("login")


# Điều hướng trang đến trang thêm khách hàng
@app.route("/add_infor_customer.html", methods=["GET", "POST"])
def add_infor_customer():
    message = ""  # Khởi tạo biến thông báo rỗng
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        countries = list(pycountry.countries)  # Lấy danh sách quốc gia
        if request.method == "POST":
            HoTen_KH = request.form["HoTen_KH"]
            NgaySinh_KH = request.form["NgaySinh_KH"]
            NgaySinh_khachhang = dt.datetime.strptime(
                NgaySinh_KH, "%Y-%m-%d"
            )  # chuyển đổi ngày sinh khách hàng thành yyyy-mm-dd
            Namsinh_khachhang = NgaySinh_khachhang.year
            # lấy thông tin từ form html
            SDT_KH = request.form["SDT_KH"]
            Email_KH = request.form["Email_KH"]
            DiaChi_KH = request.form["DiaChi_KH"]
            CMND_Passport_KH = request.form["CMND_Passport_KH"]
            QuocTich_KH = request.form["QuocTich_KH"]
            GioiTinh_KH = request.form["GioiTinh_KH"]
            # Lấy ngày tháng hiện tại dưới dạng chuỗi "yyyy-mm-dd"
            chuoi_ngay_hien_tai = dt.datetime.now().strftime("%Y-%m-%d")
            # Chuyển đổi chuỗi ngày tháng thành đối tượng datetime
            Ngay_hien_tai = dt.datetime.strptime(chuoi_ngay_hien_tai, "%Y-%m-%d")
            # Lấy năm hiện tại từ đối tượng datetime
            Nam_hien_tai = Ngay_hien_tai.year
            regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"  # kiểm tra regex email có hợp lệ
            # kiểm tra tồn tại
            sql_check_exist = "SELECT SDT_KH, Email_KH FROM khachhang WHERE SDT_KH=%s OR  Email_KH=%s"  # validate dữ liệu từ cơ sở dữ liệu
            val_check_exist = (SDT_KH, Email_KH)
            mycursor.execute(sql_check_exist, val_check_exist),
            result_check_exist = mycursor.fetchone()
            if not result_check_exist:  # kiểm tra
                if len(HoTen_KH) < 6:  # kiếm tra xem họ tên có trên 6 kí tự
                    message = "vui lòng nhập tên lớn hơn 6 kí tự "  # thông báo
                    return render_template(
                        "add_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                elif (
                    NgaySinh_khachhang > Ngay_hien_tai
                    or Nam_hien_tai - Namsinh_khachhang < 18
                ):  # kiếm tra xem ngày tháng năm sinh có lớn hơn năm ngày tháng năm sinh
                    # hiện tại và kiếm tra xem có đủ trên 18 tuổi
                    message = "vui lòng kiểm tra lại ngày tháng năm sinh, phải đảm bảo khách hàng trên 18+"  # thông báo
                    return render_template(
                        "add_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                elif (
                    len(SDT_KH) != 10 or not SDT_KH.isdigit() or int(SDT_KH[0]) != 0
                ):  # kiếm tra số điện thoại có đủ 10 kí tự và có phải là số và só đầu tiền là 0
                    message = "vui lòng kiểm tra lại số điện thoại"  # thông báo
                    return render_template(
                        "add_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                elif not re.fullmatch(
                    regex, Email_KH
                ):  # kiếm tra địa chỉ email có đúng
                    message = "vui lòng kiểm tra lại địa chỉ email"
                    return render_template(
                        "add_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                elif (
                    len(CMND_Passport_KH) != 12
                    or not CMND_Passport_KH.isdigit()
                    or int(CMND_Passport_KH[0])
                ):  # kiếm tra xem chứng minh nhân dân hoặc passport có đủ điều kiện
                    message = "vui lòng kiểm tra lại chứng minh nhân dân hoặc passport"  # thông báo
                    return render_template(
                        "add_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                else:
                    sql_insert_customer = "INSERT INTO `khachhang`( `HoTen_KH`, `NgaySinh_KH`, `SDT_KH`, `Email_KH`, `DiaChi_KH`, `CMND_Passport_KH`, `QuocTich_KH`, `GioiTinh_KH`, `TenTaiKhoan_KH`, `MatKhau_KH`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    val_insert_customer = (
                        HoTen_KH,
                        NgaySinh_khachhang,
                        SDT_KH,
                        Email_KH,
                        DiaChi_KH,
                        CMND_Passport_KH,
                        QuocTich_KH,
                        GioiTinh_KH,
                        Email_KH,
                        SDT_KH,
                    )
                    try:  # kiểm tra có lưu thành công chưa
                        mycursor.execute(sql_insert_customer, val_insert_customer)
                        mydb.commit()
                        message = "Thêm thành công"
                    except Exception as ex:
                        message = "Thêm thất bại"
                return render_template(
                    "add_infor_customer.html",
                    message=message,
                    data_country=countries,
                )
            else:
                message = "Đã tồn tại, vui lòng kiểm tra lại"
        return render_template(
            "add_infor_customer.html", message=message, data_country=countries
        )
    else:
        return redirect("login")


# Điều hướng đến trang xem chi tiết khách hàng
@app.route("/show_infor_customer/<item_id>", methods=["POST", "GET"])
def show_infor_customer(item_id):
    message = ""  # Khởi tạo biến thông báo rỗng
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql_get_edit_customter = "SELECT * FROM khachhang WHERE MAKH=%s"
        val_get_edit_customer = (item_id,)
        mycursor.execute(sql_get_edit_customter, val_get_edit_customer)
        result_get_infor_customter = mycursor.fetchone()
        return render_template(
            "show_infor_customer.html",
            message=message,
            item_id=item_id,
            data_infor_customter=result_get_infor_customter,
        )
    else:
        return redirect("login")


# Điều hướng đến trang chỉnh sửa thông tin khách hàng
@app.route("/edit_infor_customer/<item_id>", methods=["POST", "GET"])
def edit_infor_customer(item_id):
    message = ""  # Khởi tạo biến thông báo rỗng
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        countries = list(pycountry.countries)
        mycursor = mydb.cursor()
        sql_get_infor_customter = "SELECT * FROM khachhang WHERE MAKH=%s"
        val_get_infor_customer = (item_id,)
        mycursor.execute(sql_get_infor_customter, val_get_infor_customer)
        result_get_edit_customter = mycursor.fetchone()
        if request.method == "POST":
            HoTen_KH = request.form["HoTen_KH"]
            NgaySinh_KH = request.form["NgaySinh_KH"]
            NgaySinh_khachhang = dt.datetime.strptime(
                NgaySinh_KH, "%Y-%m-%d"
            )  # chuyển đổi ngày sinh khách hàng thành yyyy-mm-dd
            Namsinh_khachhang = NgaySinh_khachhang.year
            # lấy thông tin từ form html
            SDT_KH = request.form["SDT_KH"]
            Email_KH = request.form["Email_KH"]
            DiaChi_KH = request.form["DiaChi_KH"]
            CMND_Passport_KH = request.form["CMND_Passport_KH"]
            QuocTich_KH = request.form["QuocTich_KH"]
            GioiTinh_KH = request.form["GioiTinh_KH"]
            # Lấy ngày tháng hiện tại dưới dạng chuỗi "yyyy-mm-dd"
            chuoi_ngay_hien_tai = dt.datetime.now().strftime("%Y-%m-%d")
            # Chuyển đổi chuỗi ngày tháng thành đối tượng datetime
            Ngay_hien_tai = dt.datetime.strptime(chuoi_ngay_hien_tai, "%Y-%m-%d")
            # Lấy năm hiện tại từ đối tượng datetime
            Nam_hien_tai = Ngay_hien_tai.year
            regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"  # kiểm tra regex email có hợp lệ
            # kiểm tra tồn tại
            sql_check_exist = "SELECT SDT_KH, Email_KH FROM khachhang WHERE SDT_KH=%s OR  Email_KH=%s"  # validate dữ liệu từ cơ sở dữ liệu
            val_check_exist = (SDT_KH, Email_KH)
            mycursor.execute(sql_check_exist, val_check_exist),
            result_check_exist = mycursor.fetchone()
            if result_check_exist:  # kiểm tra
                if len(HoTen_KH) < 6:  # kiếm tra xem họ tên có trên 6 kí tự
                    message = "vui lòng nhập tên lớn hơn 6 kí tự "  # thông báo
                    return render_template(
                        "edit_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                elif (
                    NgaySinh_khachhang > Ngay_hien_tai
                    or Nam_hien_tai - Namsinh_khachhang < 18
                ):  # kiếm tra xem ngày tháng năm sinh có lớn hơn năm ngày tháng năm sinh
                    # hiện tại và kiếm tra xem có đủ trên 18 tuổi
                    message = "vui lòng kiểm tra lại ngày tháng năm sinh, phải đảm bảo khách hàng trên 18+"  # thông báo
                    return render_template(
                        "edit_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                elif (
                    len(SDT_KH) != 10 or not SDT_KH.isdigit() or int(SDT_KH[0]) != 0
                ):  # kiếm tra số điện thoại có đủ 10 kí tự và có phải là số và só đầu tiền là 0
                    message = "vui lòng kiểm tra lại số điện thoại"  # thông báo
                    return render_template(
                        "edit_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                elif not re.fullmatch(
                    regex, Email_KH
                ):  # kiếm tra địa chỉ email có đúng
                    message = "vui lòng kiểm tra lại địa chỉ email"
                    return render_template(
                        "edit_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                elif (
                    len(CMND_Passport_KH) != 12
                    or not CMND_Passport_KH.isdigit()
                    or int(CMND_Passport_KH[0])
                ):  # kiếm tra xem chứng minh nhân dân hoặc passport có đủ điều kiện
                    message = "vui lòng kiểm tra lại chứng minh nhân dân hoặc passport"  # thông báo
                    return render_template(
                        "edit_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                else:
                    sql_insert_customer = ""
                    val_insert_customer = (
                        HoTen_KH,
                        NgaySinh_khachhang,
                        SDT_KH,
                        Email_KH,
                        DiaChi_KH,
                        CMND_Passport_KH,
                        QuocTich_KH,
                        GioiTinh_KH,
                        Email_KH,
                        SDT_KH,
                    )
                    try:  # kiểm tra có lưu thành công chưa
                        mycursor.execute(sql_insert_customer, val_insert_customer)
                        mydb.commit()
                        message = "Thêm thành công"
                    except Exception as ex:
                        message = "Thêm thất bại"
                return render_template(
                    "edit_infor_customer.html",
                    message=message,
                    data_country=countries,
                )
            else:
                message = "Đã tồn tại, vui lòng kiểm tra lại"

           
        return render_template(
            "edit_infor_customer.html",
            message=message,
            item_id=item_id,
            data_edit_customter=result_get_edit_customter,
            data_country=countries,
        )
    else:
        return redirect("login")


# Điều hướng đến trang nhân viên
@app.route("/price.html")
def price():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM nhanvien"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("price.html", data=result)
    else:
        return redirect("login")


# Điều hướng đến trang voucher
@app.route("/contact.html")
def contact():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM voucher"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("contact.html", data=result)
    else:
        return redirect("login")


# Điều hướng trang hóa đơn thanh toán
@app.route("/map.html")
def map():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM hoadonthanhtoan"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("map.html", data=result)
    else:
        return redirect("login")


# Điều hướng đến trang hóa đơn nhà hàng
@app.route("/charts.html")
def charts():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM hoadonnhahang"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("charts.html", data=result)
    else:
        return redirect("login")


# Điều hướng trang cài đặt
@app.route("/settings.html")
def settings():
    return render_template("settings.html")


if __name__ == "__main__":
    app.run(debug=True)


# fetchone(): Phương thức này trả về dòng đầu tiên của kết quả truy vấn dưới dạng tuple hoặc None nếu không có dữ liệu nào được tìm thấy.

# fetchall(): Phương thức này trả về tất cả các dòng của kết quả truy vấn dưới dạng danh sách các tuple.

# fetchmany(size): Phương thức này trả về số lượng dòng cụ thể (được chỉ định bởi size) của kết quả truy vấn dưới dạng danh sách các tuple.
