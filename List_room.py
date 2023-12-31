import os
from flask import Flask, jsonify, request, render_template, redirect, session, url_for, Blueprint
from google.cloud import storage
import mysql.connector
import datetime as dt
import pycountry
import re

app_admin=Blueprint('admin',__name__)

# Đặt key bí mật cho phiên làm việc (session)
app_admin.secret_key = "admin"


@app_admin.route("/login.html")
def logout():
    session.pop("email", None)
    return redirect(url_for("login"))  # Điều hướng đến trang đăng nhập

# Điều hướng trang phòng
@app_admin.route("/widgets.html")
def Room():
    if "email" in session:
        print("session",session)
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        Sqlquery = "SELECT 	MAPHONG,TenPhong,LoaiPhong,DonGia,TinhTrang,GhiChu,	Imagephong FROM phong"
        mycursor.execute(
            Sqlquery,
        )
        result = mycursor.fetchall()
        mycursor.close()
        mydb.close()
        return render_template(
            "admin/widgets.html", data=result
        )  # Thêm "return" ở đây để hiển thị template
    else:
        return redirect("login.html")


@app_admin.route("/add_infor_room", methods=["GET", "POST"])
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
            # Lấy thư mục chạy ứng dụng
            app_root = os.path.dirname(os.path.abspath(__file__))

            # Tạo một đường dẫn tới thư mục tạm thời
            temporary_folder = os.path.join(app_root, "temp_files")

            # Đảm bảo thư mục tạm thời tồn tại, nếu không thì tạo nó
            if not os.path.exists(temporary_folder):
                os.makedirs(temporary_folder)

            # Tạo đường dẫn tới tệp tạm thời
            temporary_file_path = os.path.join(temporary_folder, "temporary_file.png")

            if file:
                # Lưu dữ liệu từ FileStorage vào tệp tạm thời
                file.save(temporary_file_path)

                # Tạo một client Storage
                storage_client = storage.Client.from_service_account_json(
                    "E:/path/to/your/serviceAccountKey.json"
                )

                # Xác định bucket name
                bucket_name = "image-899c9.appspot.com"

                # Lấy bucket
                bucket = storage_client.get_bucket(bucket_name)

                # Tạo tên tập tin trên Firebase Storage
                destination_blob_name = "images/" + file.filename

                # Kiểm tra sự tồn tại của tệp trên Firebase Storage
                blob = bucket.blob(destination_blob_name)
                if not blob.exists():
                    blob.upload_from_filename(
                        temporary_file_path, content_type=file.content_type
                    )
                else:
                    message = "Hình ảnh đã tồn tại"
                # Xóa tệp tạm thời
                os.remove(temporary_file_path)

                if not message:  # Chỉ thêm vào cơ sở dữ liệu nếu không có thông báo lỗi
                    # Lấy URL công khai của hình ảnh tải lên
                    image_url = blob.public_url
                    print("image_url", image_url)
                    mydb = mysql.connector.connect(
                        host="localhost", user="root", password="", database="cnpm"
                    )
                    mycursor = mydb.cursor()

                    # Kiểm tra sự tồn tại của phòng
                    sqlcheck = "SELECT MAPHONG FROM phong WHERE MAPHONG=%s"
                    val = (MAPHONG,)
                    mycursor.execute(sqlcheck, val)
                    existing_room = mycursor.fetchone()
                    if existing_room:
                        message = "Phòng đã tồn tại "
                    else:
                        sql = "INSERT INTO phong(MAPHONG, TenPhong, LoaiPhong, DonGia, TinhTrang, GhiChu, Imagephong) VALUES (%s,%s,%s,%s,%s,%s,%s)"
                        val = (
                            MAPHONG,
                            TENPHONG,
                            LOAIPHONG,
                            DONGIA,
                            TINHTRANG,
                            GHICHU,
                            image_url,
                        )
                        try:
                            mycursor.execute(sql, val)
                            mydb.commit()  # Commit thay đổi vào cơ sở dữ liệu
                            message = "Thêm thông tin phòng thành công!"  # Đặt thông báo thành công
                        except Exception as ex:
                            message = "Thêm phòng thất bại"
                            print("Lỗi " + str(ex))
            return render_template("admin/add_infor_room.html", message=message)
        return render_template("admin/add_infor_room.html", message=message)
    return redirect("login")


# Điều hướng đến trang xem chi tiết phòng
@app_admin.route("/show_infor_room/<item_id>", methods=["GET"])
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
        return render_template("admin/show_infor_room.html", data_show_room=show_room)
    else:
        return redirect("login")


# Điều hướng đến trang chỉnh sửa phòng
@app_admin.route("/edit_infor_room/<item_id>", methods=["GET", "POST"])
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
            #lấy thông tin từ form 
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
                message = "Cập nhật thông tin thành công!" # thông báo kết quả thành công 
            except Exception as e:
                message = "Cập nhật thông tin không thành công!"
        return render_template(
            "admin/edit_infor_room.html",
            item_id=item_id,
            data_edit_room=edit_room,
            message=message,
        )
    else:
        return redirect("login")


# Điều hướng xóa phòng
@app_admin.route("/delete_room/<item_id>")
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
@app_admin.route("/general_elements.html")
def general_elements():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM giahanngaythue"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("admin/general_elements.html", data=result)
    else:
        return redirect("login")


# Điều hướng đến trang chỉnh sửa gia hạn phòng
@app_admin.route("/edit_retal_date/<item_id>", methods=["GET", "POST"])
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
                    "admin/edit_retal_date.html",
                    item_id=item_id,
                    message=message,
                    data_edit_retal_date=result_show_retal_date,
                )
            elif ngay_thue_moi > ngay_thue_phong_tuong_lai:
                message = "vui lòng nhập ngày thuê mới"
                return render_template(
                    "admin/edit_retal_date.html",
                    item_id=item_id,
                    message=message,
                    data_edit_retal_date=result_show_retal_date,
                )
            elif ngay_thue_moi == ngay_thue_hien_tai:
                message = "vui lòng nhập ngày thuê mới lớn hơn ngày thuê hiện tại"
                return render_template(
                    "admin/edit_retal_date.html",
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
                    "admin/edit_retal_date.html",
                    item_id=item_id,
                    data_edit_retal_date=result_show_retal_date,
                    message=message,
                )
        return render_template(
            "admin/edit_retal_date.html",
            item_id=item_id,
            message=message,
            data_edit_retal_date=result_show_retal_date,
        )
    else:
        return redirect("login")


# Điều hướng xóa gia hạn phòng
@app_admin.route("/delete_retaldate/<item_id>")
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


# Điều hướng hủy phòng
@app_admin.route("/icons.html")
def icons():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM huythuephong"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("admin/icons.html", data=result)
    else:
        return redirect("login")


# Điều hướng đến trang chỉnh sửa hủy thuê phòng
@app_admin.route("/edit_destroy_room/<item_id>", methods=["GET", "POST"])
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
                    "admin/edit_destroy_room.html",
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
                    "admin/edit_destroy_room.html",
                    item_id=item_id,
                    destroy_room=result_show_destroy,
                    message=message,
                )
        return render_template(
            "admin/edit_destroy_room.html", item_id=item_id, destroy_room=result_show_destroy
        )
    else:
        return redirect("login")


# Điều hướng xóa hủy thuê phòng
@app_admin.route("/delete_destroy_room/<item_id>")
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
@app_admin.route("/invoice.html")
def invoice():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM thaydoiphong"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("admin/invoice.html", data=result)
    else:
        return redirect("login")


# Điều hướng đến chỉnh sửa thay đổi phòng
@app_admin.route("/edit_change_room/<item_id>", methods=["POST", "GET"])
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
                    "admin/edit_change_room.html",
                    item_id=item_id,
                    data_change_room=result_change_room,
                    message=message,
                )
            elif Ngay_thuc_hien > Ngay_thue_phong_tuong_lai:
                message = "Ngày thay đổi phải nhỏ hơn 90 ngày"
                return render_template(
                    "admin/edit_change_room.html",
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
                    "admin/edit_change_room.html",
                    item_id=item_id,
                    data_change_room=result_change_room,
                    message=message,
                )
        return render_template(
            "admin/edit_change_room.html",
            item_id=item_id,
            data_change_room=result_change_room,
            message=message,
        )
    else:
        return redirect("login")


# Điều hướng xóa thay đổi phòng
@app_admin.route("/data_change_room/<item_id>")
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
@app_admin.route("/tables.html")
def tables():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM khachhang"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("admin/tables.html", data=result)
    else:
        return redirect("login")


# Điều hướng trang đến trang thêm khách hàng
@app_admin.route("/add_infor_customer.html", methods=["GET", "POST"])
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
                        "admin/add_infor_customer.html",
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
                        "admin/add_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                elif (
                    len(SDT_KH) != 10 or not SDT_KH.isdigit() or int(SDT_KH[0]) != 0
                ):  # kiếm tra số điện thoại có đủ 10 kí tự và có phải là số và só đầu tiền là 0
                    message = "vui lòng kiểm tra lại số điện thoại"  # thông báo
                    return render_template(
                        "admin/add_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                elif not re.fullmatch(
                    regex, Email_KH
                ):  # kiếm tra địa chỉ email có đúng
                    message = "vui lòng kiểm tra lại địa chỉ email"
                    return render_template(
                        "admin/add_infor_customer.html",
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
                        "admin/add_infor_customer.html",
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
                    "admin/add_infor_customer.html",
                    message=message,
                    data_country=countries,
                )
            else:
                message = "Đã tồn tại, vui lòng kiểm tra lại"
        return render_template(
            "admin/add_infor_customer.html", message=message, data_country=countries
        )
    else:
        return redirect("login")


# Điều hướng đến trang xem chi tiết khách hàng
@app_admin.route("/show_infor_customer/<item_id>", methods=["POST", "GET"])
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
            "admin/show_infor_customer.html",
            message=message,
            item_id=item_id,
            data_infor_customter=result_get_infor_customter,
        )
    else:
        return redirect("login")


# Điều hướng đến trang chỉnh sửa thông tin khách hàng
@app_admin.route("/edit_infor_customer/<item_id>", methods=["POST", "GET"])
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
                        "admin/edit_infor_customer.html",
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
                        "admin/edit_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                elif (
                    len(SDT_KH) != 10 or not SDT_KH.isdigit() or int(SDT_KH[0]) != 0
                ):  # kiếm tra số điện thoại có đủ 10 kí tự và có phải là số và só đầu tiền là 0
                    message = "vui lòng kiểm tra lại số điện thoại"  # thông báo
                    return render_template(
                        "admin/edit_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                elif not re.fullmatch(
                    regex, Email_KH
                ):  # kiếm tra địa chỉ email có đúng
                    message = "vui lòng kiểm tra lại địa chỉ email"
                    return render_template(
                        "admin/edit_infor_customer.html",
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
                        "admin/edit_infor_customer.html",
                        message=message,
                        data_country=countries,
                    )
                else:
                    sql_update_customer = "UPDATE khachhang SET HoTen_KH=%s, NgaySinh_khachhang=%s, SDT_KH=%s,Email_KH=%s,DiaChi_KH=%s,CMND_Passport_KH=%s,QuocTich_KH=%s,GioiTinh_KH=%s,TenTaiKhoan_KH=%s"
                    val_update_customer = (
                        HoTen_KH,
                        NgaySinh_khachhang,
                        SDT_KH,
                        Email_KH,
                        DiaChi_KH,
                        CMND_Passport_KH,
                        QuocTich_KH,
                        GioiTinh_KH,
                        Email_KH,
                    )
                    try:  # kiểm tra có lưu thành công chưa
                        mycursor.execute(sql_update_customer, val_update_customer)
                        mydb.commit()
                        message = "Thêm thành công"
                    except Exception as ex:
                        message = "Thêm thất bại"
                return render_template(
                    "admin/edit_infor_customer.html",
                    message=message,
                    data_country=countries,
                )
            else:
                message = "Đã tồn tại, vui lòng kiểm tra lại"

        return render_template(
            "admin/edit_infor_customer.html",
            message=message,
            item_id=item_id,
            data_edit_customter=result_get_edit_customter,
            data_country=countries,
        )
    else:
        return redirect("login")


# xóa thông tin trang khách hàng
@app_admin.route("/delete_infor_customer/<item_id>")
def delete_infor_customer(item_id):
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "DELETE FROM khachhang WHERE MAKH  = %s"
        val = (item_id,)  # Đảm bảo val là một tuple chứa giá trị item_id
        try:
            mycursor.execute(sql, val)
            mydb.commit()
        except Exception as ex:
            print("lỗi", str(ex))
        # Sau khi xóa phòng, bạn có thể chuyển hướng người dùng đến trang khách hàng hoặc bất kỳ trang nào bạn muốn.
        return redirect("tables")
    else:
        return redirect("login")


# Điều hướng đến trang nhân viên
@app_admin.route("/price.html")
def price():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM nhanvien"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("admin/price.html", data=result)
    else:
        return redirect("login")


# Điều hướng trang đến trang xem chi tiết nhân viên
@app_admin.route("/show_infor_employee/<item_id>", methods=["POST", "GET"])
def show_infor_employee(item_id):
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql_show_infor_employee = "SELECT * FROM nhanvien WHERE MANV=%s"
        val_show_infor_employee = (item_id,)
        mycursor.execute(sql_show_infor_employee, val_show_infor_employee)
        result_show_infor_employee = mycursor.fetchone()
        return render_template(
            "admin/show_infor_employee.html",
            item_id=item_id,
            data_show_infor_employee=result_show_infor_employee,
        )
    else:
        return redirect("login")


# Điều hướng đến trang thêm nhân viên
@app_admin.route("/add_infor_employees.html", methods=["POST", "GET"])
def add_infor_employees():
    message = ""
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        if request.method == "POST":
            # lấy dữ liệu từ trang add-infor_employee
            HoTen_NV = request.form["HoTen_NV"]
            NgaySinh_NV = request.form["NgaySinh_NV"]
            NgaySinh_nhanvien = dt.datetime.strptime(
                NgaySinh_NV, "%Y-%m-%d"
            )  # chuyền đổi ngày sinh nhân viên thành năm-tháng-ngày
            namsinh_nhanvien = NgaySinh_nhanvien.year
            chuoi_ngay_hien_tai = dt.datetime.now().strftime(
                "%Y-%m-%d"
            )  # Lấy ngày tháng hiện tại dưới dạng chuỗi "yyyy-mm-dd"
            Ngay_hien_tai = dt.datetime.strptime(
                chuoi_ngay_hien_tai, "%Y-%m-%d"
            )  # Chuyển đổi chuỗi ngày tháng thành đối tượng datetime
            Nam_hien_tai = Ngay_hien_tai.year  # Lấy năm hiện tại từ đối tượng datetime
            ChucVu_NV = request.form["ChucVu_NV"]
            SDT_NV = request.form["SDT_NV"]
            Email_NV = request.form["Email_NV"]
            regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"  # ký tự đặc biệt của email
            DiaChi_NV = request.form["DiaChi_NV"]
            GioiTinh_NV = request.form["GioiTinh_NV"]
            NgayBatDauLamViec = request.form["NgayBatDauLamViec"]
            NBĐLV = dt.datetime.strptime(NgayBatDauLamViec, "%Y-%m-%d")
            # kiểm tra có trùng dữ liệu
            sql_check_infor_employees = (
                "SELECT SDT_NV,Email_NV FROM nhanvien WHERE SDT_NV=%s AND Email_NV=%s"
            )
            val_check_infor_empoyees = (SDT_NV, Email_NV)
            check_exits = mycursor.execute(
                sql_check_infor_employees, val_check_infor_empoyees
            )
            mycursor.reset()
            if check_exits:
                message = "Thông tin đã tồn tại vui lòng kiếm tra lại"  # thông báo thông tin đã tồn tại
            else:
                if len(HoTen_NV) < 6:
                    message = "Tên phải lớn hơn 6 ký tự"
                    return render_template(
                        "admin/add_infor_employees.html", message=message
                    )  # trả về thông kết quả
                elif (
                    NgaySinh_nhanvien > Ngay_hien_tai
                    or Nam_hien_tai - namsinh_nhanvien < 18
                ):
                    # thông báo kiếm tra ngày tháng năm sinh
                    message = "Nhân viên phải trên 18 tuổi và ngày tháng năm sinh không được lớn hơn ngày tháng năm hiện tại"
                    return render_template(
                        "admin/add_infor_employees.html", message=message
                    )  # trả về kết quả
                elif (
                    len(SDT_NV) != 10 or not SDT_NV.isdigit() or int(SDT_NV[0]) != 0
                ):  # kiếm tra số điện thoại có đủ 10 kí tự và có phải là số và só đầu tiền là 0
                    message = "số điện thoại có đủ 10 kí tự và có phải là số và só đầu tiền là 0"
                    return render_template(
                        "admin/add_infor_employees.html", message=message
                    )  # trả về kết quả
                elif re.fullmatch(Email_NV, regex):  # kiêm tra email có hợp lệ
                    message = "Địa chỉ email không hợp lệ"
                    return render_template(
                        "admin/add_infor_employees.html", message=message
                    )  # trả về kết quả
                elif len(ChucVu_NV) == 0:  # kiểm tra chức vụ có rỗng không
                    message = "chức vụ không được đẻ rỗng "  # thông báo
                    return render_template(
                        "admin/add_infor_employees.html", message=message
                    )  # trả về kết quả
                elif len(DiaChi_NV) < 10:  # kiêm tra xem địa chỉ có 10 ký tự.
                    message = "Địa chỉ phải hơn 10 ký tự"  # thông báo
                    return render_template(
                        "admin/add_infor_employees.html", message=message
                    )  # trả về kết quả
                elif len(GioiTinh_NV) == 0:  # kiêm tra giói tính nhân viên có rỗng.
                    message = "Địa chỉ phải hơn 10 ký tự"  # thông báo
                    return render_template(
                        "admin/add_infor_employees.html", message=message
                    )  # trả về kết quả
                elif (
                    NBĐLV < Ngay_hien_tai
                ):  # kiểm tra ngày bắt đầu làm việc phải lớn hơn hoặc bằng ngày hiện tại
                    message = "ngày bắt đầu làm việc phải lớn hơn hoặc bằng ngày hiện tại"  # thông báo
                    return render_template(
                        "admin/add_infor_employees.html", message=message
                    )  # trả về kết quả
                else:  # thỏa mãn mọi điều kiện thực hiện câu lệnh insert dữ liệu vào database
                    ma = None  # Đặt giá trị mặc định cho biến 'ma'
                    # Kiểm tra và thiết lập giá trị mã 'ma' dựa trên 'ChucVu_NV'
                    if ChucVu_NV == "Giám Đốc":
                        ma = "GĐ"
                    elif ChucVu_NV == "Quản lý":
                        ma = "QL"
                    elif ChucVu_NV == "Lễ Tân":
                        ma = "LT"
                    elif ChucVu_NV == "Phục Vụ Phòng":
                        ma = "PVP"
                    elif ChucVu_NV == "Phục vụ bàn":
                        ma = "PVB"
                    elif ChucVu_NV == "Thu Ngân":
                        ma = "TN"
                    else:
                        message = "Lỗi không tìm thấy"
                    # Kiểm tra nếu 'ma' không phải là None
                    if ma is not None:
                        last_number = 1
                        new_macvnv = f"{ma}{last_number:03d}"
                        print(new_macvnv)
                        # Thực hiện truy vấn kiểm tra 'MACVNV' đã tồn tại hay chưa
                        sql_check_macvnv = (
                            "SELECT MACVNV FROM nhanvien WHERE MACVNV = %s"
                        )
                        val_check_macvnv = (new_macvnv,)
                        mycursor.execute(sql_check_macvnv, val_check_macvnv)
                        result_check_macvnv = mycursor.fetchone()
                        # Kiểm tra kết quả của truy vấn kiểm tra
                        if result_check_macvnv:
                            # Bản ghi đã tồn tại, xử lý tương ứng
                            sql_check_exits_macvnv = "SELECT MACVNV FROM nhanvien ORDER BY MACVNV DESC LIMIT 1"
                            mycursor.execute(sql_check_exits_macvnv)
                            result = mycursor.fetchone()
                            if result:
                                last_number = int(result[0][len(ma) :])
                                new_number = last_number + 1
                                new_macvnv = f"{ma}{new_number:03d}"
                                print(new_macvnv)
                        else:
                            last_number = 1
                            new_macvnv = f"{ma}{last_number:03d}"
                            print(new_macvnv)
                    else:
                        message = "Mã none"
                    sql_insert_infor_employees = "INSERT INTO `nhanvien`(`MACVNV`, `HoTen_NV`, `NgaySinh_NV`, `ChucVu_NV`, `SDT_NV`, `Email_NV`, `DiaChi_NV`, `GioiTinh_NV`, `NgayBatDauLamViec`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    val_insert_infor_employees = (
                        new_macvnv,
                        HoTen_NV,
                        NgaySinh_nhanvien,
                        ChucVu_NV,
                        SDT_NV,
                        Email_NV,
                        DiaChi_NV,
                        GioiTinh_NV,
                        NgayBatDauLamViec,
                    )
                    try:
                        mycursor.execute(
                            sql_insert_infor_employees, val_insert_infor_employees
                        )
                        mydb.commit()
                        message = "Thêm thành công"
                    except Exception as ex:
                        message = "Lỗi thêm"
                        print(ex)
            return render_template(
                "admin/add_infor_employees.html", message=message
            )  # trả về kết quả
        return render_template("admin/add_infor_employees.html")
    else:
        return redirect("login")


# Điều hướng đến trang chỉnh sửa thông tin nhân viên
@app_admin.route("/edit_infor_employee/<item_id>", methods=["POST", "GET"])
def edit_infor_employee(item_id):
    message = ""
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql_select_infor_employees = "SELECT * FROM nhanvien WHERE MANV=%s"
        val_select_infor_empoyees = (item_id,)
        mycursor.execute(sql_select_infor_employees, val_select_infor_empoyees)
        Get_infor_employee = mycursor.fetchone()
        if request.method == "POST":
            # lấy dữ liệu từ trang add-infor_employee
            HoTen_NV = request.form["HoTen_NV"]
            NgaySinh_NV = request.form["NgaySinh_NV"]
            NgaySinh_nhanvien = dt.datetime.strptime(
                NgaySinh_NV, "%Y-%m-%d"
            )  # chuyền đổi ngày sinh nhân viên thành năm-tháng-ngày
            namsinh_nhanvien = NgaySinh_nhanvien.year
            chuoi_ngay_hien_tai = dt.datetime.now().strftime(
                "%Y-%m-%d"
            )  # Lấy ngày tháng hiện tại dưới dạng chuỗi "yyyy-mm-dd"
            Ngay_hien_tai = dt.datetime.strptime(
                chuoi_ngay_hien_tai, "%Y-%m-%d"
            )  # Chuyển đổi chuỗi ngày tháng thành đối tượng datetime
            Nam_hien_tai = Ngay_hien_tai.year  # Lấy năm hiện tại từ đối tượng datetime
            Lamviecsau30ngay = dt.timedelta(days=30)
            ChucVu_NV = request.form["ChucVu_NV"]
            SDT_NV = request.form["SDT_NV"]
            Email_NV = request.form["Email_NV"]
            regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"  # ký tự đặc biệt của email
            DiaChi_NV = request.form["DiaChi_NV"]
            GioiTinh_NV = request.form["GioiTinh_NV"]
            NgayBatDauLamViec = request.form["NgayBatDauLamViec"]
            NBĐLV = dt.datetime.strptime(NgayBatDauLamViec, "%Y-%m-%d")
            if len(HoTen_NV) < 6:
                message = "Tên phải lớn hơn 6 ký tự"
                return render_template(
                    "admin/edit_infor_employee.html",
                    message=message,
                    result_Get_infor_employee=Get_infor_employee,
                )  # trả về kết quả
            elif (
                NgaySinh_nhanvien > Ngay_hien_tai
                or Nam_hien_tai - namsinh_nhanvien < 18
            ):
                # thông báo kiếm tra ngày tháng năm sinh
                message = "Nhân viên phải trên 18 tuổi và ngày tháng năm sinh không được lớn hơn ngày tháng năm hiện tại"
                return render_template(
                    "admin/edit_infor_employee.html",
                    message=message,
                    result_Get_infor_employee=Get_infor_employee,
                )  # trả về kết quả
            elif (
                len(SDT_NV) != 10 or not SDT_NV.isdigit() or int(SDT_NV[0]) != 0
            ):  # kiếm tra số điện thoại có đủ 10 kí tự và có phải là số và só đầu tiền là 0
                message = (
                    "số điện thoại có đủ 10 kí tự và có phải là số và só đầu tiền là 0"
                )
                return render_template(
                    "admin/edit_infor_employee.html",
                    message=message,
                    result_Get_infor_employee=Get_infor_employee,
                )  # trả về kết quả
            elif re.fullmatch(Email_NV, regex):  # kiêm tra email có hợp lệ
                message = "Địa chỉ email không hợp lệ"
                return render_template(
                    "admin/edit_infor_employee.html",
                    message=message,
                    result_Get_infor_employee=Get_infor_employee,
                )  # trả về kết quả
            elif len(ChucVu_NV) == 0:  # kiểm tra chức vụ có rỗng không
                message = "chức vụ không được đẻ rỗng "  # thông báo
                return render_template(
                    "admin/edit_infor_employee.html",
                    message=message,
                    result_Get_infor_employee=Get_infor_employee,
                )  # trả về kết quả
            elif len(DiaChi_NV) < 10:  # kiêm tra xem địa chỉ có 10 ký tự.
                message = "Địa chỉ phải hơn 10 ký tự"  # thông báo
                return render_template(
                    "admin/edit_infor_employee.html",
                    message=message,
                    result_Get_infor_employee=Get_infor_employee,
                )  # trả về kết quả
            elif len(GioiTinh_NV) == 0:  # kiêm tra giói tính nhân viên có rỗng.
                message = "Địa chỉ phải hơn 10 ký tự"  # thông báo
                return render_template(
                    "admin/edit_infor_employee.html",
                    message=message,
                    result_Get_infor_employee=Get_infor_employee,
                )  # trả về kết quả
            elif (
                Ngay_hien_tai - NBĐLV < Lamviecsau30ngay
            ):  # kiểm tra ngày bắt đầu làm việc phải lớn hơn hoặc bằng ngày hiện tại
                message = "ngày bắt đầu làm việc phải lớn hơn hoặc bằng ngày hiện tại"  # thông báo
                return render_template(
                    "admin/edit_infor_employee.html",
                    message=message,
                    result_Get_infor_employee=Get_infor_employee,
                )  # trả về kết quả
            else:
                ma = None  # Đặt giá trị mặc định cho biến 'ma'
                # Kiểm tra và thiết lập giá trị mã 'ma' dựa trên 'ChucVu_NV'
                if ChucVu_NV == "Giám Đốc":
                    ma = "GĐ"
                elif ChucVu_NV == "Quản lý":
                    ma = "QL"
                elif ChucVu_NV == "Lễ Tân":
                    ma = "LT"
                elif ChucVu_NV == "Phục Vụ Phòng":
                    ma = "PVP"
                elif ChucVu_NV == "Phục vụ bàn":
                    ma = "PVB"
                elif ChucVu_NV == "Thu Ngân":
                    ma = "TN"
                else:
                    message = "Lỗi không tìm thấy"
                    # Kiểm tra nếu 'ma' không phải là None
                if ma is not None:
                    last_number = 1
                    new_macvnv = f"{ma}{last_number:03d}"
                    print(new_macvnv)
                    # Thực hiện truy vấn kiểm tra 'MACVNV' đã tồn tại hay chưa
                    sql_check_macvnv = "SELECT MACVNV FROM nhanvien WHERE MACVNV = %s"
                    val_check_macvnv = (new_macvnv,)
                    mycursor.execute(sql_check_macvnv, val_check_macvnv)
                    result_check_macvnv = mycursor.fetchone()
                    # Kiểm tra kết quả của truy vấn kiểm tra
                    if result_check_macvnv:
                        # Bản ghi đã tồn tại, xử lý tương ứng
                        sql_check_exits_macvnv = (
                            "SELECT MACVNV FROM nhanvien ORDER BY MACVNV DESC LIMIT 1"
                        )
                        mycursor.execute(sql_check_exits_macvnv)
                        result = mycursor.fetchone()
                        if result:
                            last_number = int(result[0][len(ma) :])
                            new_number = last_number + 1
                            new_macvnv = f"{ma}{new_number:03d}"
                            print(new_macvnv)
                    else:
                        last_number = 1
                        new_macvnv = f"{ma}{last_number:03d}"
                        print(new_macvnv)
                else:
                    message = "Mã none"

                sql_update_infor_employee = "UPDATE `nhanvien` SET `MACVNV`=%s,`HoTen_NV`=%s,`NgaySinh_NV`=%s,`ChucVu_NV`=%s,`SDT_NV`=%s,`Email_NV`=%s,`DiaChi_NV`=%s,`GioiTinh_NV`=%s,`NgayBatDauLamViec`=%s WHERE MANV=%s"
                val_update_infor_employee = (
                    new_macvnv,
                    HoTen_NV,
                    NgaySinh_nhanvien,
                    ChucVu_NV,
                    SDT_NV,
                    Email_NV,
                    DiaChi_NV,
                    GioiTinh_NV,
                    NBĐLV,
                    item_id,
                )
                print(sql_update_infor_employee)
                print(val_update_infor_employee)
                try:
                    mycursor.execute(
                        sql_update_infor_employee, val_update_infor_employee
                    )
                    mydb.commit()
                    message = "Cập nhật thành công"
                except Exception as ex:
                    message = "Cập nhật thất bại: " + str(ex)
                    print(ex)
            return render_template(
                "admin/edit_infor_employee.html",
                message=message,
                result_Get_infor_employee=Get_infor_employee,
                item_id=item_id,
            )
        return render_template(
            "admin/edit_infor_employee.html",
            result_Get_infor_employee=Get_infor_employee,
            item_id=item_id,
        )
    else:
        return redirect("login")


# Xóa thông tin nhân viên
@app_admin.route("/delete_infor_employees/<item_id>")
def delete_infor_employees(item_id):
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql_delete_infor_employees = "DELETE FROM `nhanvien` WHERE MANV=%s"
        val_delete_infor_employees = (item_id,)
        mycursor.execute(sql_delete_infor_employees, val_delete_infor_employees)
        mydb.commit()
        return redirect("price")
    else:
        return redirect("login")


# hiển thị trang phiếu thuê phòng
@app_admin.route("/contact.html")
def contact():
    # iconClicked = False
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        # Lấy thông tin từ bảng phieuthuephong kết hợp với bảng phong thông qua trường MAPHONG
        sql = "SELECT * FROM phieuthuephong"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("admin/contact.html", data=result)
    else:
        return redirect("login")

# update tổng tiền tự động
@app_admin.route("/update_total_price", methods=["POST"])
def update_total_price():
    selected_room = request.get_json().get(
        "selected_room"
    )  # Lấy giá trị Mã Phòng từ yêu cầu POST
    print(selected_room)
    mydb = mysql.connector.connect(
        host="localhost", user="root", password="", database="cnpm"
    )
    mycursor = mydb.cursor()
    try:
        sql_get_dongia = "SELECT DonGia FROM phong WHERE stt = %s"
        # print("sql", sql_get_dongia)
        val_get_dongia = (selected_room,)
        mycursor.execute(sql_get_dongia, val_get_dongia)
        row = mycursor.fetchone()
        # print("row is: ", row)
        if row is not None:
            total_price = row[0]
            return jsonify({"total_price": total_price})
        else:
            return jsonify({"total_price": None})
    except Exception as e:
        # Xử lý lỗi ở đây, ví dụ in ra thông báo lỗi:
        print("Lỗi: ", str(e))
        return jsonify(
            {"total_price": None}
        )  # Hoặc trả về giá trị mặc định hoặc thông báo lỗi khác.


# Điều hướng đến trang tạo hóa đơn
@app_admin.route("/add_infor_roomretalvoucher.html", methods=["POST", "GET"])
def add_infor_roomretalvoucher():
    message = ""
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        # # Get thông tin phòng
        sql_get_room = "SELECT MAPHONG,stt FROM phong"
        mycursor.execute(
            sql_get_room,
        )
        result_get_room = mycursor.fetchall()
        # Get thông tin khách hàng
        sql_get_customers = "SELECT Email_KH, MAKH FROM khachhang"
        mycursor.execute(
            sql_get_customers,
        )
        result_get_customers = mycursor.fetchall()
        regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"  # ký tự đặc biệt của email
        # lây thông tin khách hàng điền từ form
        if request.method == "POST":
            HinhThucThanhToan = request.form[
                "HinhThucThanhToan"
            ]  # lấy thông tin của hình thức thanh toán
            NgayNhanPhong = request.form[
                "NgayNhanPhong"
            ]  # lấy thông ti của ngày nhận phòng
            # Lấy năm hiện tại
            current_year = dt.datetime.now().year

            # Thêm 1 để có năm tiếp theo
            next_year = current_year + 1

            # chuyển đổi ngày nhận phòng từ chuỗi qua thời gian
            NgayNhanPhong_moi = dt.datetime.strptime(NgayNhanPhong, "%Y-%m-%d")

            # chuyền đổi ngày nhận phòng thành yyyy-mm-dd và lấy ngày hiện tại trên máy tính
            Ngayhientai = dt.datetime.now()

            NgayTraPhong = request.form[
                "NgayTraPhong"
            ]  # lấy thông tin của ngày trả phòng
            # chuyền đổi thông tin ngày trả phòng từ chuỗi qua thời gian
            NgayTraPhong_moi = dt.datetime.strptime(NgayTraPhong, "%Y-%m-%d")
            SoLuongNguoiLon = request.form[
                "SoLuongNguoiLon"
            ]  # lấy thông tin số lượng người lớn
            SoLuongTreEm = int(
                request.form["SoLuongTreEm"]
            )  # lấy thông tin số lượng trẻ em
            TongTien = request.form["TongTien"]  # lấy thông tin tổng tiền
            # loại bỏ các kí tự không phải số
            Tongtien_str = "".join(filter(str.isdigit, TongTien))
            Tongtienmoi = float(Tongtien_str)
            GhiChu = request.form["GhiChu"]  # lấy thông tin ghi chú
            MAKH = request.form["MAKH"]  # lấy thông tin mã khách hàng
            print("MAKH", MAKH)
            Maphong = request.form["Maphong"]  # lấy thông tin mã phòng
            if NgayNhanPhong_moi <= Ngayhientai or current_year > next_year:
                message = "vui lòng kiểm tra lại ngày nhận phòng, ngày nhận phòng phải nhỏ hơn năm hiện tại"
                return render_template(
                    "admin/add_infor_roomretalvoucher.html",
                    result_get_infor=result_get_room,
                    result_get_customers=result_get_customers,
                    message=message,
                )
                #
            if (
                NgayTraPhong_moi > (Ngayhientai + dt.timedelta(days=30))
                or NgayTraPhong_moi < NgayNhanPhong_moi
            ):
                message = "vui lòng kiểm tra lại ngày trả phòng, ngày trả phòng không được quá 30 ngày"
                return render_template(
                    "admin/add_infor_roomretalvoucher.html",
                    result_get_infor=result_get_room,
                    result_get_customers=result_get_customers,
                    message=message,
                )
            if SoLuongTreEm > 1 and SoLuongNguoiLon >= 2:
                Tongtienmoi = Tongtienmoi * (20 / 100)
                print("tongtienmoi", Tongtienmoi)
            if SoLuongTreEm >= 2 and SoLuongNguoiLon > 1:
                Tongtienmoi = Tongtienmoi * (20 / 100)
                print("tongtienmoi", Tongtienmoi)
            if re.fullmatch(MAKH, regex):
                message = "Địa chỉ email không hợp lệ"
                return render_template(
                    "admin/add_infor_roomretalvoucher.html",
                    result_get_infor=result_get_room,
                    result_get_customers=result_get_customers,
                    message=message,
                )
                # kiểm tra email tồn tại hay chưa
            sql_check_email = "SELECT MAKH FROM khachhang WHERE Email_KH=%s"
            val_check_enail = (MAKH,)
            mycursor.execute(sql_check_email, val_check_enail)
            check_email = mycursor.fetchone()
            print("check_email", check_email)
            if check_email:
                MAKH = check_email[0]
            else:
                sql_insert_infor_khachhang = (
                    "INSERT INTO `khachhang`(`Email_KH`) VALUES (%s)"
                )
                val_insert_infor_khachhang = (MAKH,)
                mycursor.execute(sql_insert_infor_khachhang, val_insert_infor_khachhang)
                mydb.commit()
                MAKH = mycursor.lastrowid
                print(MAKH)
            print(Maphong)
            sql_get_stt = "SELECT stt FROM phong WHERE stt=%s"
            val_get_stt = (Maphong,)
            mycursor.execute(sql_get_stt, val_get_stt)
            row = mycursor.fetchone()
            print("row", row)
            Maphong = row[0]
            print(Maphong)
            # kiểm tra phong đã có trong phiếu thuê phòng
            get_kiemtra_maphong = "SELECT Maphong FROM phieuthuephong WHERE Maphong=%s"
            val_kiemtra_maphong = (Maphong,)
            mycursor.execute(get_kiemtra_maphong, val_kiemtra_maphong)
            kiemtra_maphong = mycursor.fetchone()
            if kiemtra_maphong:
                message = "Phòng đã được đặt"
                return render_template(
                    "admin/add_infor_roomretalvoucher.html",
                    result_get_infor=result_get_room,
                    result_get_customers=result_get_customers,
                    message=message,
                )
            else:
                sql_insert_infor_roomretalvoucher = "INSERT INTO `phieuthuephong`(`HinhThucThanhToan`, `NgayNhanPhong`, `NgayTraPhong`, `SoLuongNguoiLon`, `SoLuongTreEm`, `TongTien`, `GhiChu`, `CHECKIN`,`MANV`, `MAKH`, `Maphong`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                val_insert_infor_roomretalvoucher = (
                    HinhThucThanhToan,
                    NgayNhanPhong_moi,
                    NgayTraPhong_moi,
                    SoLuongNguoiLon,
                    SoLuongTreEm,
                    Tongtienmoi,
                    GhiChu,
                    "check",
                    None,
                    MAKH,
                    Maphong,
                )
                try:
                    mycursor.execute(
                        sql_insert_infor_roomretalvoucher,
                        val_insert_infor_roomretalvoucher,
                    )
                    mydb.commit()
                    message = "Tạo thành công"
                except Exception as e:
                    message = "Tạo thất bại"
                    print("Lỗi ", str(e))
                print(message)
                return redirect("contact.html")
        return render_template(
            "admin/add_infor_roomretalvoucher.html",
            result_get_infor=result_get_room,
            result_get_customers=result_get_customers,
            message=message,
        )
    else:
        return redirect("login")


# chấp nhận thông tin khách hàng
@app_admin.route("/reciveIconClicked/<item_id>", methods=["POST", "GET"])
def reciveIconClicked(item_id):
    message = ""
    if "email" in session:
        data = request.get_json()
        iconClicked = data.get("iconClicked")
        print("click_accept(item_id):", iconClicked, item_id)
        print("data", data)
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        if iconClicked == True:
            sql_update_again_phieuthuephong = (
                "UPDATE `phieuthuephong` SET `CHECKIN`=%s WHERE `MAPTP`=%s"
            )
            val_update_again_phieuthuephong = ("check", item_id)
            try:
                mycursor.execute(
                    sql_update_again_phieuthuephong, val_update_again_phieuthuephong
                )
                mydb.commit()
                message = "thành công"
                session["message"] = message
            except Exception as ex:
                print("Lỗi ", str(ex))
            return redirect(url_for("contact"))
        else:
            sql_update_again_phieuthuephong = (
                "UPDATE `phieuthuephong` SET `CHECKIN`=%s WHERE `MAPTP`=%s"
            )
            val_update_again_phieuthuephong = ("not check", item_id)
            try:
                mycursor.execute(
                    sql_update_again_phieuthuephong, val_update_again_phieuthuephong
                )
                mydb.commit()
                message = "thất bại"
                session["message"] = message
            except Exception as ex:
                print("Lỗi ", str(ex))
            return redirect(url_for("contact"))
    else:
        return redirect("login")


# lấy thông tin phòng checkbox
@app_admin.route("/checkboxdata", methods=["POST", "GET"])
def checkboxdata():
   
    if "email" in session:
        data = request.get_json()
        checkboxdata = data.get("selectedIds")
        print("checkboxdata", checkboxdata)
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        success = True  # Mặc định là thành công
        # Lặp qua danh sách checkboxdata và kiểm tra trạng thái "CHECKIN" của từng phòng
        for maphong in checkboxdata:
            sql_checkbox_checkphieuthuephong = f"SELECT CHECKIN,HinhThucThanhToan,TongTien,MAKH,MAPTP FROM phieuthuephong WHERE MAPTP = {maphong}"
            mycursor.execute(sql_checkbox_checkphieuthuephong)
            row = mycursor.fetchone()
            print("checkin ", row)
            if row and row[0] == "not check":
                print("false")
                return jsonify(success=False)
            HinhThucThanhToan = row[1]
            TongTien = row[2]
            MAKH = row[3]
            MAPTP = row[4]
            SoTienPhuThem = 0
            GhiChu = None
            sql_checkbox_getkhachhang = (
                f"SELECT HoTen_KH FROM khachhang WHERE MAKH={MAKH}"
            )
            mycursor.execute(sql_checkbox_getkhachhang)
            get_name_khachhang = mycursor.fetchone()
            Name_client = get_name_khachhang[0]
            print("name khách hàng + ", Name_client)
            print("HinhThucThanhToan", HinhThucThanhToan)
        # check tồn tại
        sql_check_insert_hoadon = f"SELECT * FROM hoadonthanhtoan WHERE MAptp={maphong}"
        mycursor.execute(
            sql_check_insert_hoadon,
        )
        check_insert_hoadon_exist =mycursor.fetchone()
        if check_insert_hoadon_exist:
            return jsonify(success=False)
        else:
            sql_insert_hoadon = "INSERT INTO `hoadonthanhtoan`(`HinhThucThanhToan`, `SoTienPhuThem`, `TongTienThanhToan`, `NguoiThanhToan`, `GhiChu`, `MAptp`, `MAHDNH`) VALUES (%s,%s,%s,%s,%s,%s,%s)"
            val_insert_hoadon = (
                HinhThucThanhToan,
                SoTienPhuThem,
                TongTien,
                Name_client,
                GhiChu,
                MAPTP,
                None,
            )
            try:
                mycursor.execute(sql_insert_hoadon, val_insert_hoadon)
                mydb.commit()
               
            except Exception as ex:
                print("Lỗi ", str(ex))
                success = False
        if success:
            return jsonify(success=True)
        else:
            return jsonify(success=False)
    else:
        return redirect("login")


# xóa thông tin phiếu thuê phòng
@app_admin.route("/delete_infor_rentalroom/<item_id>")
def delete_infor_rentalroom(item_id):
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql_get_makhachhang = "SELECT MAKH FROM phieuthuephong WHERE MAPTP=%s"
        val_get_makhachhang = (item_id,)
        mycursor.execute(sql_get_makhachhang, val_get_makhachhang)
        row_khachhang = mycursor.fetchone()
        # xóa thông tin phiếu thuê phòng
        sql_delete_phieuthuephong = "DELETE FROM `phieuthuephong` WHERE MAPTP=%s"
        val_delete_phieuthuephong = (item_id,)
        try:
            mycursor.execute(sql_delete_phieuthuephong, val_delete_phieuthuephong)
            mydb.commit()
            print("Xóa thành công")
        except Exception as e:
            print("Lỗi:", str(e))
        # xóa thông tin khách hàng trùng với phiếu thuê phòng
        sql_delete_khachhang = "DELETE FROM `khachhang` WHERE MAKH=%s"
        val_delete_khachhang = (row_khachhang[0],)
        try:
            mycursor.execute(sql_delete_khachhang, val_delete_khachhang)
            mydb.commit()
            print("Xóa thành công")
        except Exception as e:
            print("Lỗi:", str(e))
        return redirect("contact")
    else:
        return redirect("login")


# Điều hướng tình trạng phòng
@app_admin.route("/media_gallery.html")
def media_gallery():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql_get_status_phong = "SELECT * FROM phong ORDER BY LoaiPhong ASC"
        mycursor.execute(sql_get_status_phong)
        result_status = mycursor.fetchall()

        sql_get_status_phieu = "SELECT DISTINCT Maphong FROM phieuthuephong"
        mycursor.execute(sql_get_status_phieu)
        result_status_phieu = mycursor.fetchall()
        if result_status:
            stt = [status[0] for status in result_status]
            maphieuthuephong = [statusphieu[0] for statusphieu in result_status_phieu]
            print("maphieuthuephongs", maphieuthuephong)
            print("stt của phòng", stt)  # CHECKIN='check' AND
            sql_status_phiethuephong = "SELECT * FROM phieuthuephong WHERE CHECKIN='check' AND Maphong IN ({})".format(
                ", ".join(["%s"] * len(stt))
            )
            print("sql_status_phiethuephong", sql_status_phiethuephong)
            val_status_phiethuephong = stt
            mycursor.execute(sql_status_phiethuephong, val_status_phiethuephong)
            result_status_phieuthuephong = mycursor.fetchall()
            if result_status_phieuthuephong:
                print(result_status_phieuthuephong)
                CHECKIN = [checkin[9] for checkin in result_status_phieuthuephong]
                Maphong = [Maphong[12] for Maphong in result_status_phieuthuephong]
                print("CHECKIN", CHECKIN)
                print("Maphong", Maphong)

                # status = [maphong for maphong in stt if maphong in Maphong]
                # print("status",status)
                if "check" in CHECKIN:
                    status = Maphong
            return render_template(
                "admin/media_gallery.html",
                result_status=result_status,
                checkstatus=status,
                phongstt=maphieuthuephong,
            )
        else:
            # Xử lý khi không có dòng nào được trả về (tuỳ theo yêu cầu của bạn)
            return "Không có dữ liệu phòng thuê."
    else:
        return redirect("login")


@app_admin.route("/map.html")
def map():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM hoadonthanhtoan"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("admin/map.html", data=result)
    else:
        return redirect("login")

# Điều hướng đến trang xem hóa đơn
@app_admin.route("/show_infor_bill/<item_id>", methods=["GET", "POST"])
def show_infor_bill(item_id):
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql_show_infor_bill = "SELECT * FROM hoadonthanhtoan WHERE MAHD=%s"
        val_show_infor_bill = (item_id,)
        mycursor.execute(sql_show_infor_bill, val_show_infor_bill)
        result_show_infor_bill = mycursor.fetchone()
        return render_template(
            "admin/show_infor_bill.html",
            item_id=item_id,
            show_infor_bill=result_show_infor_bill,
        )
    else:
        return redirect("login")

# Điều hướng trang chỉnh sửa thông tin hóa đơn 
@app_admin.route("/edit_infor_bill/<item_id>", methods=["POST","GET"])
def edit_infor_bill(item_id):
    message = ""
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql_show_infor_bill = "SELECT * FROM hoadonthanhtoan WHERE MAHD=%s"
        val_show_infor_bill = (item_id,)
        mycursor.execute(sql_show_infor_bill, val_show_infor_bill)
        result_edit_infor_bill = mycursor.fetchone()
        if request.method=="POST":
            HinhThucThanhToan=request.form["HinhThucThanhToan"]
            TongTienThanhToan=request.form["TongTienThanhToan"]
            SoTienPhuThem=request.form["SoTienPhuThem"]
            NguoiThanhToan=request.form["NguoiThanhToan"]
            GhiChu=request.form["GhiChu"]
            MAptp=request.form["MAptp"]
            MAHDNH=request.form["MAHDNH"]
            if float(TongTienThanhToan)<0:
                message="Please enter again money"
                return render_template("admin/edit_infor_bill.html",  result_edit_infor_bill= result_edit_infor_bill, message=message)
            elif float(SoTienPhuThem)<0:
                message="Please enter again money and money > 0 "
                return render_template("admin/edit_infor_bill.html",  result_edit_infor_bill= result_edit_infor_bill, message=message)
            else:
                sql_update_hoadon="UPDATE `hoadonthanhtoan` SET `HinhThucThanhToan`=%s,`SoTienPhuThem`=%s,`TongTienThanhToan`=%s,`NguoiThanhToan`=%s,`GhiChu`=%s,`MAptp`=%s,`MAHDNH`=%s WHERE MAHD =%s"
                val_update_hoadon=(HinhThucThanhToan,SoTienPhuThem,TongTienThanhToan,NguoiThanhToan,GhiChu,MAptp,MAHDNH,item_id,)
                try:
                    mycursor.execute(sql_update_hoadon,val_update_hoadon)
                    mydb.commit()
                    message="Update successful"
                except Exception as ex:
                    print("Lỗi update hóa đơn ", str(ex))
                    message="Error update"
        return render_template("admin/edit_infor_bill.html",  result_edit_infor_bill= result_edit_infor_bill, message=message)
    else:
        return redirect("login")
# xóa hóa đơn
@app_admin.route("/delete_bill/<item_id>")
def delete_bill(item_id):
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        # lấy thông tin hóa đơn
        sql_get_hoadon="SELECT MAptp FROM `hoadonthanhtoan` WHERE MAHD=%s"
        val_get_hoadon=(item_id,)
        mycursor.execute(sql_get_hoadon, val_get_hoadon)
        row_hoadon=mycursor.fetchone()
        print("row_hoadon ",row_hoadon)
        # lấy mã khách hàng từ bảng khách hàng
        sql_get_makhachhang = "SELECT MAKH FROM phieuthuephong WHERE MAPTP=%s"
        val_get_makhachhang = (row_hoadon[0],)
        mycursor.execute(sql_get_makhachhang, val_get_makhachhang)
        row_khachhang = mycursor.fetchone()
        #xóa thông tin hóa đơn
        sql_delete_bill="DELETE FROM `hoadonthanhtoan` WHERE MAHD=%s"
        val_delete_bill=(item_id,)
        try:
            mycursor.execute(sql_delete_bill,val_delete_bill,)
            mydb.commit()
            print("Xóa thành công hóa đơn")
        except Exception as ex:
            print("Lỗi bill ", str(ex))
        # xóa thông tin phiếu thuê phòng
        sql_delete_phieuthuephong = "DELETE FROM `phieuthuephong` WHERE MAPTP=%s"
        val_delete_phieuthuephong = (row_hoadon[0],)
        try:
            mycursor.execute(sql_delete_phieuthuephong, val_delete_phieuthuephong)
            mydb.commit()
            print("Xóa thành công phiếu thuê phòng")
        except Exception as e:
            print("Lỗi:", str(e))
        # xóa thông tin khách hàng trùng với phiếu thuê phòng
        sql_delete_khachhang = "DELETE FROM `khachhang` WHERE MAKH=%s"
        val_delete_khachhang = (row_khachhang[0],)
        try:
            mycursor.execute(sql_delete_khachhang, val_delete_khachhang)
            mydb.commit()
            print("Xóa thành công khách hàng")
        except Exception as e:
            print("Lỗi:", str(e))
        return redirect("map")
    else:
        return redirect("login")

# Điều hướng đến trang thêm hóa đơn nhà hàng
@app_admin.route("/charts.html")
def charts():
    if "email" in session:
        mydb = mysql.connector.connect(
            host="localhost", user="root", password="", database="cnpm"
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM hoadonnhahang"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return render_template("admin/charts.html", data=result)
    else:
        return redirect("login")

# Điều hướng trang cài đặt
@app_admin.route("/settings.html")
def settings():
    return render_template("settings.html")


# if __name__ == "__main__":
#     app_admin.run(debug=True)


# fetchone(): Phương thức này trả về dòng đầu tiên của kết quả truy vấn dưới dạng tuple hoặc None nếu không có dữ liệu nào được tìm thấy.

# fetchall(): Phương thức này trả về tất cả các dòng của kết quả truy vấn dưới dạng danh sách các tuple.

# fetchmany(size): Phương thức này trả về số lượng dòng cụ thể (được chỉ định bởi size) của kết quả truy vấn dưới dạng danh sách các tuple.


# thông tin mã voucher
# sql_get_voucher = "SELECT * FROM voucher"
# mycursor.execute(sql_get_voucher)
# row = mycursor.fetchall()
# print("row voucher: ", row)  # in thông tin của voucher lấy được
# if len(row) > 0:
#     check_voucher = row[0][0]  # lấy mã voucher
#     gia_tri_voucher = int(row[0][1])  # lấy giá trị của voucher
#     ngay_het_han_voucher = row[0][2]  # lấy ngày hết hạn của voucher
#     ngay_phat_hanh_voucher = row[0][3]  # lấy  ngày phát hàng voucher
#     so_luong_voucher = int(row[0][4])  # lấy số lượng voucher
# # lấy ngày hiện tại của voucher
# ngay_hien_tai_voucher = dt.datetime.now().strftime("%Y-%m-%d")

# kiểm tra xem thông tin đăng nhập của manager
# @app.route("/", methods=["GET", "POST"])
# def login():
#      # Đường dẫn đầy đủ đến thư mục user
#     if request.method == "POST":
#         email = request.form["email"]
#         password = request.form["password"]

#         mydb = mysql.connector.connect(
#             host="localhost",
#             user="root",
#             password="",
#             database="cnpm",
#         )
#         mycursor = mydb.cursor()
#         query = f"SELECT Namelogin, passwordlogin FROM adminmanager WHERE Namelogin = '{email}' AND passwordlogin = '{password}'"
#         mycursor.execute(query)
#         myresult = mycursor.fetchone()

#         # if myresult:
#         #     session["email"] = email
#         #     return redirect(
#         #         url_for("Room")
#         #     )  # Điều hướng đến trang Room khi đăng nhập thành công

#     return render_template("admin/login.html")

