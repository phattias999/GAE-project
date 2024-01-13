import os
from flask import Flask, jsonify, request, render_template, redirect, session, url_for
import mysql.connector, re
import datetime as dt
from List_room import app_admin
import pycountry

# tạo một đối tượng của lớp
app_user = Flask(__name__, template_folder="templates")
app_user.register_blueprint(app_admin, url_prefix="/admin")
# Đặt key bí mật cho phiên làm việc (session)
app_user.secret_key = "admin"


# hàm kết nối tới database
def connect_to_database():
    return mysql.connector.connect(
        host="localhost", user="root", password="", database="cnpm"
    )


# hàm trả về 404
def not_found():
    return render_template("user/404.html")


@app_user.route("/")
def index():
    return redirect(url_for("home"))


# hàm trả về session lấy thông tin khách hàng
def get_information_customer_session_mail(email_in_session):
    mydb = connect_to_database()
    mycursor = mydb.cursor()
    name_user_email = session["email"]
    
    sql_get_infor_login="SELECT `id_khach_hang` FROM `loginuser` WHERE username=%s"
    val_get_infor_login=(name_user_email,)
    mycursor.execute(sql_get_infor_login,val_get_infor_login)
    get_id_customer=mycursor.fetchone()
    cusomter_id=get_id_customer[0]

    # print("session trong email", name_user_email)
    sql_get_name_customer = "SELECT HoTen_KH FROM khachhang WHERE MAKH=%s"
    val_get_name_customer = (cusomter_id,)
    mycursor.execute(sql_get_name_customer, val_get_name_customer)
    get_Name = mycursor.fetchone()
    # print("get_Name ", get_Name)
    get_Name_customer = get_Name[0]
    Tach_name = get_Name_customer.split()
    if len(Tach_name) >= 2:
        last_name = " ".join(Tach_name[1:])
        return last_name
    else:
        last_name = get_Name_customer
        return last_name


# màn hình chính của trang web index
@app_user.route("/index.html", methods=["GET", "POST"])
def home():
    mydb = connect_to_database()
    mycursor = mydb.cursor()

    if "email" in session:
        name_user_email = session["email"]
        # print("session trong email", name_user_email)

        # lấy tên khách hàng hiên thị lên màn hình khi đăng nhập email
        last_name = get_information_customer_session_mail(name_user_email)
       
        sql_get_room_in_index = "(SELECT * FROM phong WHERE LoaiPhong = 'A' ORDER BY RAND() LIMIT 1) UNION (SELECT * FROM phong WHERE LoaiPhong = 'B' ORDER BY RAND() LIMIT 1) UNION ( SELECT * FROM phong WHERE LoaiPhong = 'C' ORDER BY RAND() LIMIT 1 ) ORDER BY RAND() LIMIT 3"
        mycursor.execute(sql_get_room_in_index)
        result_get_room_in_index = mycursor.fetchall()
        mycursor.close()
        mydb.close()
    else:
        last_name = None

        sql_get_room_in_index = "(SELECT * FROM phong WHERE LoaiPhong = 'A' ORDER BY RAND() LIMIT 1) UNION (SELECT * FROM phong WHERE LoaiPhong = 'B' ORDER BY RAND() LIMIT 1) UNION ( SELECT * FROM phong WHERE LoaiPhong = 'C' ORDER BY RAND() LIMIT 1 ) ORDER BY RAND() LIMIT 3"
        mycursor.execute(sql_get_room_in_index)
        result_get_room_in_index = mycursor.fetchall()
        mycursor.close()
        mydb.close()
    if result_get_room_in_index:
        return render_template(
            "user/index.html",
            data_result_index=result_get_room_in_index,
            data_name=last_name,
        )
    else:
        return not_found()


# form điền thông tin thuê phòng
@app_user.route("/rent_room/<item_id>", methods=["GET", "POST"])
def rent_room(item_id):
    message = " "
    mydb = connect_to_database()  # hàm kết nối databse
    mycursor = mydb.cursor()
    sql_receive_data = "SELECT * FROM phong WHERE stt=%s"  # hàm truy vấn dữ liệu
    val_receive_data = (item_id,)
    mycursor.execute(sql_receive_data, val_receive_data)
    result_receive_data = mycursor.fetchone()
    countries = list(pycountry.countries)

    # hàm lấy thong tin phòng
    def get_room_info(item_id):
        sql_receive_data = "SELECT * FROM phong WHERE stt=%s"
        val_receive_data = (item_id,)
        mycursor.execute(sql_receive_data, val_receive_data)
        return mycursor.fetchone()

    # hàm lấy thông tin khách hàng
    def get_customer_info(email):
        sql_get_all_customer = "SELECT * FROM khachhang WHERE Email_KH=%s"
        val_get_all_customer = (email,)
        mycursor.execute(sql_get_all_customer, val_get_all_customer)
        return mycursor.fetchone()

    def insert_rent_room_info(
        checkin_in_strptime,
        checkin_out_strptime,
        sum_adults,
        sum_all_children,
        sum_all_rent_room,
        notes,
        customer_id,
        item_id,
        AmountRooms,
    ):
        insert_rentroom_query = "INSERT INTO `phieuthuephong`(`HinhThucThanhToan`, `NgayNhanPhong`, `NgayTraPhong`, `SoLuongNguoiLon`, `SoLuongTreEm`, `TongTien`, `GhiChu`, `CHECKIN`, `MANV`, `MAKH`, `Maphong`, `soluongphong`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val_rentroom = (
            "Trực Tiếp",
            checkin_in_strptime,
            checkin_out_strptime,
            sum_adults,
            sum_all_children,
            sum_all_rent_room,
            notes,
            "not check",
            None,
            customer_id,
            item_id,
            AmountRooms,
        )
        mycursor.execute(insert_rentroom_query, val_rentroom)
        mydb.commit()

     # kiểm tra tài khoản khách hàng tồn tại hay chưa
    def check_customer(email_user):
        # thêm dữ liệu vào bảng khách hàng
        check_khachhang = "SELECT SDT_KH,Email_KH,TenTaiKhoan_KH FROM khachhang WHERE Email_KH=%s"
        val_check_khachhang = (email_user,)
        mycursor.execute(check_khachhang, val_check_khachhang)
        return mycursor.fetchone()  
    
    def get_information_customer(email_user):
        # lấy thông tin tài khoản khách hàng
        sql_get_infor_login="SELECT `id_khach_hang` FROM `loginuser` WHERE username=%s"
        val_get_infor_login=(email_user,)
        mycursor.execute(sql_get_infor_login,val_get_infor_login)
        return mycursor.fetchone()

    def update_table_customers(name,phone, email, countries,gender,id_customers):
        sql_update_customer = "UPDATE `khachhang` SET `HoTen_KH`=%s,`SDT_KH`=%s,`Email_KH`=%s,`QuocTich_KH`=%s,`GioiTinh_KH`=%s WHERE MAKH=%s"
        val_update_customer = (name,phone, email,countries,gender,id_customers)
        mycursor.execute(sql_update_customer,val_update_customer)
        mydb.commit()

    if "email" in session:
        # email của session
        name_user_email = session["email"]

        last_name = get_information_customer_session_mail(name_user_email)

        # hiển thị thông tin trong lastname
        get_all = get_customer_info(name_user_email)
        # print("get_all ", get_all)

        result_receive_data = get_room_info(item_id)
        money_per_night = result_receive_data[4]  # lấy thong tin tiền từ phòng

        # hàm trả về lại trang
        def re_turn():
            return render_template(
                "user/rent_room.html",
                data_receive=result_receive_data,
                message=message,
                item_id=item_id,
                data_country=countries,
            )

        if request.method == "POST":
            name = request.form["name"]
            print("name",str(name))
            if name < "4" or name == " ":  # câu lệnh kiểm tra tên
                message = "Please enter your name again"
                # print("lỗi tên")  # in lỗi tên
                return re_turn()  # trả về một hàm

            phone = request.form["phone"]
            # print("phone", phone)
            regexPhone = r"^0(3[2-9]|7[0-9]|8[1-9]|9[0-9]|12[0-9])\d{7}$"
            if ( not re.match(regexPhone, phone) or phone == " "):  # câu lệnh kiểm tra số điện thoại việt nam
                message = "Please enter your phone number again"
                # print(" lỗi số điện thoại")
                return re_turn()

            regexEmail = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            email = request.form["email"]
            if not re.match(regexEmail, email) or email == " ":
                message = "Please enter your email again"
                # print("lỗi email")
                return re_turn()

            AmountRooms = int(request.form["AmountRooms"])
            # print("AmountRooms", AmountRooms)  # in số lượng
            if AmountRooms == 0:  # câu lệnh kiểm tra số lượng phòng
                message = "Please choose amount rooms"
                print("lỗi ", AmountRooms)  # in lỗi số lượng
                return re_turn()

            checkin_in = request.form["check_in"]
            # print("checkin", checkin_in)  # in ngày checkin
            # dùng strptime để chuyển chuỗi checkin-in thành datetime
            checkin_in_strptime = dt.datetime.strptime(checkin_in, "%d/%m/%Y")
            # print("checkin_in_strptime", checkin_in_strptime)

            checkin_out = request.form["check_out"]
            # print("checkout", checkin_out)
            # dùng strptime để chuyển chuỗi checkin-out thành datetime
            checkin_out_strptime = dt.datetime.strptime(checkin_out, "%d/%m/%Y")
            # print("checkin_out_strptime", checkin_out_strptime)

            # lấy dữ liệu thông tin chọn quốc tịch
            nationality = request.form["nationality"]
            # print("nationality", nationality)  # in thông tin quốc gia
            if nationality == "0":
                message = "Please choose countries"
                return re_turn()

            # lấy dữ liệu gender
            gender = request.form["gender"]
            # print("gender", gender)

            # câu lệnh lấy số lượng của form người lớn và trẻ em
            sumAdults = 0
            sumChildren = 0
            sumInfants = 0
            for i in range(AmountRooms):
                adults = int(request.form[f"adults{i + 1}"])
                print("adults", str(adults))
                sumAdults += adults  # tính tống số lượng người lớn
                print("adults", str(adults))

                children = int(request.form[f"children{i+1}"])
                print("children", str(children))
                sumChildren += children  # tính tổng số lượng trẻ em
                print("sumChildren", str(sumChildren))

                infants = int(request.form[f"infants{i+1}"])
                print("infants", str(infants))
                sumInfants += infants  # tính tổng số lượng em bé
                print("infants", str(infants))

            sumallchildren = sumChildren + sumInfants
            # print("tổng số lượng các bé", sumallchildren)

            # print("tổng số lượng người lớn: ", sumAdults)
            notes = request.form["message"]

            # tổng tiền phòng cuối cùng
            sum_all_rent_room = AmountRooms * money_per_night

            # lấy id đăng nhập của người dùng
            get_id_customers= get_information_customer(name_user_email)
            id_customers_getfor_login=get_id_customers[0]
            update_table_customers(name, phone,email,nationality,gender,id_customers_getfor_login)
            if mycursor.rowcount>0:
                insert_rent_room_info(checkin_in_strptime,checkin_out_strptime,sumAdults,sumallchildren,sum_all_rent_room,notes,id_customers_getfor_login,item_id,AmountRooms)
                print("thêm thông tin thành công")
                return redirect(url_for("booking_success"))
            else:
                print("lỗi đặt phòng")
                return render_template("user/404.html")
        return render_template(
            "user/rent_room.html",
            data_receive=result_receive_data,
            data_name=last_name,
            data_infor=get_all,
            data_country=countries,
        )
    else:
        result_receive_data = get_room_info(item_id)
        money_per_night = result_receive_data[4]  # lấy thong tin tiền từ phòng

        def re_turn():
            return render_template(
                "user/rent_room.html",
                data_receive=result_receive_data,
                message=message,
                item_id=item_id,
                data_country=countries,
            )

        if request.method == "POST":
            name = request.form["name"]
            if name < "4" or name == " ":  # câu lệnh kiểm tra tên
                message = "Please enter your name again"
                # print("lỗi tên")  # in lỗi tên
                return re_turn()  # trả về một hàm

            phone = request.form["phone"]
            # print("phoen", phone)
            regexPhone = r"^0(3[2-9]|7[0-9]|8[1-9]|9[0-9]|12[0-9])\d{7}$"
            if (
                not re.match(regexPhone, phone) or phone == " "
            ):  # câu lệnh kiểm tra số điện thoại việt nam
                message = "Please enter your phone number again"
                # print("lỗi số điện thoại")
                return re_turn()

            regexEmail = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            email = request.form["email"]
            if not re.match(regexEmail, email) or email == " ":
                message = "Please enter your email again"
                # print("lỗi email")
                return re_turn()

            AmountRooms = int(request.form["AmountRooms"])
            # print("AmountRooms", AmountRooms)  # in số lượng
            if AmountRooms == 0:  # câu lệnh kiểm tra số lượng phòng
                message = "Please choose amount rooms"
                # print("lỗi ", AmountRooms)  # in lỗi số lượng
                return re_turn()

            checkin_in = request.form["check_in"]
            # print("checkin", checkin_in)  # in ngày checkin
            # dùng strptime để chuyển chuỗi checkin-in thành datetime
            checkin_in_strptime = dt.datetime.strptime(checkin_in, "%d/%m/%Y")
            # print("checkin_in_strptime", checkin_in_strptime)

            checkin_out = request.form["check_out"]
            # print("checkout", checkin_out)
            # dùng strptime để chuyển chuỗi checkin-out thành datetime
            checkin_out_strptime = dt.datetime.strptime(checkin_out, "%d/%m/%Y")
            # print("checkin_out_strptime", checkin_out_strptime)

            # lấy dữ liệu thông tin chọn quốc tịch
            nationality = request.form["nationality"]
            # print("nationality", nationality)  # in thông tin quốc gia
            if nationality == "0":
                message = "Please choose countries"
                return re_turn()

            # lấy dữ liệu gender
            gender = request.form["gender"]
            # print("gender", gender)

            # câu lệnh lấy số lượng của form người lớn và trẻ em
            sumAdults = 0
            sumChildren = 0
            sumInfants = 0
            for i in range(AmountRooms):
                adults = int(request.form[f"adults{i + 1}"])
                # print("adults", str(adults))
                sumAdults += adults  # tính tống số lượng người lớn
                # print("adults", str(adults))

                children = int(request.form[f"children{i+1}"])
                # print("children", str(children))
                sumChildren += children  # tính tổng số lượng trẻ em
                # print("sumChildren", str(sumChildren))

                infants = int(request.form[f"infants{i+1}"])
                # print("infants", str(infants))
                sumInfants += infants  # tính tổng số lượng em bé
                # print("infants", str(infants))

            sumallchildren = sumChildren + sumInfants
            # print("tổng số lượng các bé", sumallchildren)

            # print("tổng số lượng người lớn: ", sumAdults)
            notes = request.form["message"]

            # tổng tiền phòng cuối cùng
            sum_all_rent_room = AmountRooms * money_per_night
            if check_customer(email):
                message="Plase login account to booking"
                return re_turn()
            # create information customer
            sql_insert_infor_customer = "INSERT INTO `khachhang`( `HoTen_KH`, `SDT_KH`, `Email_KH`, `QuocTich_KH`, `GioiTinh_KH`) VALUES (%s,%s,%s,%s,%s)"
            val_insert_infor_customer = (name, phone, email, nationality, gender)

            # kiểm tra xem dữ liệu khách hàng đã được thêm vào hay chưa nếu
            try:
                mycursor.execute(sql_insert_infor_customer, val_insert_infor_customer)
                # lấyy id mới được từ bảng khách hàng thêm vào
                newly_added_id = mycursor.lastrowid
                # print("newly_added_id_khachhang", newly_added_id)
                mydb.commit()
                # thêm dữ liệu vào login user
                sql_insert_loginuser = "INSERT INTO `loginuser`(`id_khach_hang`, `username`, `password`) VALUES (%s,%s,%s)"
                val_insert_loginuser = (newly_added_id, email, phone)
                mycursor.execute(sql_insert_loginuser, val_insert_loginuser)
                mydb.commit()
                if mycursor.rowcount:
                    insert_rent_room_info(
                        checkin_in_strptime,
                        checkin_out_strptime,
                        sumAdults,
                        sumallchildren,
                        sum_all_rent_room,
                        notes,
                        newly_added_id,
                        item_id,
                        AmountRooms,
                    )
                    print("thêm thành công")
                    return redirect(url_for("booking_success"))
                else:
                    print("thêm thất bại")
                    return render_template("user/404.html")
            except Exception as e:
                print("lỗi thông tin ", str(e))
        return render_template(
            "user/rent_room.html",
            data_receive=result_receive_data,
            data_country=countries,
        )


# trang đặt phòng thành công
@app_user.route("/booking_success.html")
def booking_success():
    return render_template("user/booking_success.html")


# điều hướng đến trang about
@app_user.route("/about.html")
def about():
    if "email" in session:
        name_user_email = session["email"]
        last_name = get_information_customer_session_mail(name_user_email)
        return render_template("user/about.html", data_name=last_name)
    else:
        return render_template("user/about.html")


# điều hướng đến trang contact
@app_user.route("/contact.html")
def contact():
    return render_template("user/contact.html")


# điều hướng tới trang sự kiên (events)
@app_user.route("/events.html")
def events():
    if "email" in session:
        name_user_email = session["email"]
        last_name = get_information_customer_session_mail(name_user_email)
        return render_template("user/events.html", data_name=last_name)
    else:
        return render_template("user/events.html")


# điều hướng đên trang đặt chỗ (reservation)
@app_user.route("/reservation.html")
def reservation():
    mydb=connect_to_database()
    mycursor=mydb.cursor()
    if "email" in session:
        name_user_email = session["email"]
        last_name = get_information_customer_session_mail(name_user_email)

        # lấy id của bảng login 
        sql_get_user_name_table_login="SELECT `id_khach_hang` FROM `loginuser` WHERE username=%s"
        val_get_user_name_table_login=(name_user_email,)
        mycursor.execute(sql_get_user_name_table_login,val_get_user_name_table_login)
        get_id_user=mycursor.fetchone()
        Id_User=get_id_user[0]

        # lấy thông tin khách hàng
        sql_get_table_customers="SELECT * FROM `khachhang` WHERE MAKH =%s"
        val_get_table_customers=(Id_User,)
        mycursor.execute(sql_get_table_customers,val_get_table_customers)
        Get_customer_infor=mycursor.fetchall()

        # lấy thông tin của bảng phiếu thuê phòng
        sql_get_table_rent_rooms="SELECT * FROM `phieuthuephong` WHERE MAKH=%s"
        val_get_table_rent_rooms=(Id_User,)
        mycursor.execute(sql_get_table_rent_rooms,val_get_table_rent_rooms)
        Get_rent_room=mycursor.fetchall()
       
        combined_info = {
            'Get_customer_infor': Get_customer_infor,
            'Get_rent_room': Get_rent_room
        }
        if Get_rent_room:
            return render_template("user/reservation.html",data_name=last_name,combined_info=combined_info,notify=True)
        else:
            return render_template("user/reservation.html",data_name=last_name,)
        
   
# điều hướng tới trang phòng (rooms)
@app_user.route("/rooms.html", methods=["GET","POST"])
def rooms():
    mydb = connect_to_database()
    mycursor = mydb.cursor()
    def get_rooms():
        sql_get_room = "(SELECT * FROM phong WHERE LoaiPhong = 'A' ORDER BY RAND() LIMIT 2) UNION (SELECT * FROM phong WHERE LoaiPhong = 'B' ORDER BY RAND() LIMIT 2) UNION ( SELECT * FROM phong WHERE LoaiPhong = 'C' ORDER BY RAND() LIMIT 2 ) ORDER BY RAND() LIMIT 6"
        mycursor.execute(sql_get_room)
        return mycursor.fetchall()
    
    # lấy thông tin một phòng
    def Get_one_room():
        sql_get_room = "SELECT * FROM phong ORDER BY RAND() LIMIT 1"
        mycursor.execute(sql_get_room)
        return mycursor.fetchall()
    
    def Get_two_room():
        sql_get_room = "SELECT * FROM phong ORDER BY RAND() LIMIT 1"
        mycursor.execute(sql_get_room)
        return mycursor.fetchall()
    
    if "email" in session:
        name_user_email = session["email"]

        # lấy tên khách hàng hiên thị lên màn hình khi đăng nhập email
        last_name = get_information_customer_session_mail(name_user_email)
        # lấy thông tin phòng
        Get_rooms=get_rooms()
      
        One_room=Get_one_room()
        Two_rooms=Get_two_room()
        mycursor.close()
        mydb.close()
    else:
        last_name = None
        Get_rooms=get_rooms()
     
        One_room=Get_one_room()
        Two_rooms=Get_two_room()
        mycursor.close()
        mydb.close()
    if Get_rooms:
        return render_template(
            "user/rooms.html",
            get_Rooms=Get_rooms,
            data_name=last_name,One_room=One_room,Two_rooms=Two_rooms
        )
    else:
        return not_found()


# điều hướng tới tranh danh sách các phòng
@app_user.route("/listroom.html")
def listroom():
    mydb = connect_to_database()
    mycursor = mydb.cursor()
    if "email" in session:
        name_user_email = session["email"]
        last_name = get_information_customer_session_mail(name_user_email)
    else:
        last_name = None

    sql_get_data_listroom = "SELECT * FROM phong WHERE TinhTrang=%s"
    val_get_data_listroom = ("None",)
    mycursor.execute(
        sql_get_data_listroom,
        val_get_data_listroom,
    )
    result_get_data_listroom = mycursor.fetchall()
    print("result_get_data_listroom", result_get_data_listroom)

    if result_get_data_listroom:
        return render_template(
            "user/listroom.html", data=result_get_data_listroom, data_name=last_name
        )
    else:
        return not_found()


# điều hướng tới trang đăng nhập
@app_user.route("/login.html", methods=["GET", "POST"])
def login():
    mydb = connect_to_database()
    mycursor = mydb.cursor()
    if request.method == "POST":
        email_admin_or_customer = request.form["email"]
        print(" email_admin" + email_admin_or_customer)
        password_admin_or_customer = request.form["password"]
        sql_login_admin = "SELECT Namelogin, passwordlogin FROM adminmanager WHERE Namelogin=%s AND passwordlogin=%s"
        val_login_admin = (email_admin_or_customer, password_admin_or_customer)
        mycursor.execute(sql_login_admin, val_login_admin)
        result_login_admin = mycursor.fetchone()
        print("result_login", str(result_login_admin))
        if result_login_admin:
            session["email"] = email_admin_or_customer
            print("session", session)
            return redirect(url_for("admin.Room"))
        else:
            sql_login_customer = "SELECT  `username`, `password` FROM `loginuser` WHERE username=%s AND password=%s"
            val_login_customer = (email_admin_or_customer, password_admin_or_customer)
            mycursor.execute(sql_login_customer, val_login_customer)
            result_login_customer = mycursor.fetchone()
            if result_login_customer:
                session["email"] = email_admin_or_customer
                return redirect(url_for("home"))
    return render_template("user/login.html")


@app_user.route("/logout", methods=["GET"])
def logout_customer():
    if "email" in session:
        session.pop("email", None)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app_user.run(debug=True)


# Sử dụng strptime để chuyển đổi chuỗi ngày thành đối tượng datetime.
# Sử dụng strftime để định dạng lại đối tượng datetime thành chuỗi mới với định dạng "%Y-%m-%d"
