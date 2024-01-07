import os
from flask import Flask, jsonify, request, render_template, redirect, session, url_for
import mysql.connector,re
import datetime as dt
from List_room import app_admin
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
#tạo một đối tượng của lớp
app_user=Flask(__name__, template_folder='templates')
app_user.register_blueprint(app_admin, url_prefix='/admin')
# Đặt key bí mật cho phiên làm việc (session)
app_user.secret_key = "admin"


#hàm kết nối tới database
def connect_to_database():
    return mysql.connector.connect(
        host="localhost", user="root", password="", database="cnpm"
    )

# hàm trả về 404
def not_found():
    return render_template('user/404.html')

@app_user.route("/")
def index():
    return redirect(url_for("home"))

# màn hình chính của trang web index
@app_user.route("/index.html", methods=["GET","POST"])
def home():
    mydb=connect_to_database()
    mycursor=mydb.cursor()
    sql_get_room_in_index="(SELECT * FROM phong WHERE LoaiPhong = 'A' ORDER BY RAND() LIMIT 1) UNION (SELECT * FROM phong WHERE LoaiPhong = 'B' ORDER BY RAND() LIMIT 1) UNION ( SELECT * FROM phong WHERE LoaiPhong = 'C' ORDER BY RAND() LIMIT 1 ) ORDER BY RAND() LIMIT 3"
    mycursor.execute(sql_get_room_in_index)
    result_get_room_in_index=mycursor.fetchall()
    mycursor.close()
    mydb.close()
    return render_template("user/index.html", data_result_index=result_get_room_in_index)

#form điền thông tin thuê phòng
@app_user.route("/rent_room/<item_id>", methods=["GET","POST"])
def rent_room(item_id):
    message=" "
    mydb=connect_to_database() #hàm kết nối databse  
    mycursor=mydb.cursor()
    sql_receive_data="SELECT * FROM phong WHERE stt=%s" # hàm truy vấn dữ liệu 
    val_receive_data=(item_id,)
    mycursor.execute(sql_receive_data,val_receive_data)
    result_receive_data=mycursor.fetchone()
    money_per_night=result_receive_data[4] # lấy thong tin tiền từ phòng 
    print("moneypernight: ", money_per_night) # in thông tin tiền
    print("kết quả là: ", str(result_receive_data)) # in thong tin kết quả lấy toàn bị dữ liệu
    print("item_id", item_id)
    # hàm trả về lại trang
    def re_turn():
        return render_template("user/rent_room.html", data_receive=result_receive_data,message=message, item_id=item_id)
    if request.method=="POST":
        name=request.form["name"]
        # if name<'4' or name==" ":  # câu lệnh kiểm tra tên
        #     message="Please enter your name again"
        #     print("lỗi tên") # in lỗi tên 
        #     return  re_turn() # trả về một hàm 
        
        phone=request.form["phone"] 
        # print("phoen", phone)
        # regexPhone = r"^0(3[2-9]|7[0-9]|8[1-9]|9[0-9]|12[0-9])\d{7}$"
        # if not re.match(regexPhone,phone) or phone== " ": # câu lệnh kiểm tra số điện thoại việt nam
        #     message="Please enter your phone number again"
        #     print("lỗi số điện thoại")
        #     return re_turn()
        
        regexEmail=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        email=request.form["email"]
        # if not re.match(regexEmail,email) or email==" ":
        #     message="Please enter your email again"
        #     print("lỗi email")
        #     return re_turn()

        AmountRooms=int(request.form["AmountRooms"])
        print("AmountRooms",   AmountRooms) # in số lượng 
        if AmountRooms==0: # câu lệnh kiểm tra số lượng phòng 
            message="Please choose amount rooms"
            print("lỗi ", AmountRooms) # in lỗi số lượng
            return re_turn()

        checkin_in=request.form["check_in"]
        print("checkin", checkin_in) # in ngày checkin 
        #dùng strptime để chuyển chuỗi checkin-in thành datetime
        checkin_in_strptime = dt.datetime.strptime(checkin_in, "%d/%m/%Y")
        print("checkin_in_strptime",checkin_in_strptime) 


        checkin_out=request.form["check_out"]
        print("checkout", checkin_out)
        #dùng strptime để chuyển chuỗi checkin-out thành datetime
        checkin_out_strptime=dt.datetime.strptime(checkin_out, "%d/%m/%Y")
        print("checkin_out_strptime",checkin_out_strptime)

        # lấy dữ liệu thông tin chọn quốc tịch
        nationality=request.form["nationality"]
        print("nationality",nationality) # in thông tin quốc gia
        if nationality=="0":
            message="Please choose countries"
            return re_turn()
        
        # lấy dữ liệu gender
        gender=request.form["gender"]
        print("gender",gender)
        
        # câu lệnh lấy số lượng của form người lớn và trẻ em
        sumAdults=0
        sumChildren=0 
        sumInfants=0
        for i in range(AmountRooms):
            adults=int(request.form[f'adults{i + 1}'])
            print("adults",str(adults))
            sumAdults+=adults # tính tống số lượng người lớn
            print("adults",str(adults))

            children=int(request.form[f'children{i+1}'])
            print("children",str(children))
            sumChildren+=children # tính tổng số lượng trẻ em
            print("sumChildren",str(sumChildren))

            infants=int(request.form[f'infants{i+1}'])
            print("infants",str(infants))
            sumInfants+=infants # tính tổng số lượng em bé
            print("infants",str(infants))
        

        print("tổng số lượng các bé", sumChildren+sumInfants)
        print("tổng số lượng người lớn: ", sumAdults)
        notes=request.form["message"]
        
        # thêm dữ liệu vào bảng khách hàng
        check_khachhang="SELECT SDT_KH,	Email_KH,TenTaiKhoan_KH FROM khachhang WHERE SDT_KH=%s OR Email_KH=%s OR TenTaiKhoan_KH=%s"
        val_check_khachhang=(phone,email,email,)
        mycursor.execute(check_khachhang,val_check_khachhang)
        check_in_khachhang=mycursor.fetchone()
        if check_in_khachhang:
            message="your account already exits please login acount"
            return re_turn()
        else:
            # thêm thông tin khách hàng
            insert_infor_customers="INSERT INTO `khachhang`(`HoTen_KH`,  `SDT_KH`, `Email_KH`, `QuocTich_KH`,`GioiTinh_KH`, `TenTaiKhoan_KH`, `MatKhau_KH`) VALUES (%s,%s,%s,%s,%s,%s,%s)"
            val_insert_infor_customers=(name,phone,email,nationality,gender,email,phone)
            check_insert_customer= mycursor.execute(insert_infor_customers,val_insert_infor_customers)
            print("thêm khách hàng thành công ở rentroom: ",check_insert_customer )
            mydb.commit()
            Newid_khachhang=mycursor.lastrowid

           
    return render_template("user/rent_room.html", data_receive=result_receive_data)

# điều hướng đến trang about
@app_user.route("/about.html")
def about():
    return render_template("user/about.html")

# điều hướng đến trang contact 
@app_user.route("/contact.html")
def contact():
    return render_template("user/contact.html")

# điều hướng tới trang sự kiên (events) 
@app_user.route("/events.html")
def events():
    return render_template("user/events.html")

# điều hướng đên trang đặt chỗ (reservation)
@app_user.route("/reservation.html")
def reservation():
    return render_template("user/reservation.html")

# điều hướng tới trang phòng (rooms)
@app_user.route("/rooms.html")
def rooms():
    mydb=connect_to_database()
    mycursor=mydb.cursor()
    return render_template("user/rooms.html")

#điều hướng tới tranh danh sách các phòng
@app_user.route("/listroom.html")
def listroom():
    mydb=connect_to_database()
    mycursor=mydb.cursor()
    sql_get_data_listroom="SELECT * FROM phong WHERE TinhTrang=%s"
    val_get_data_listroom=("None",)
    mycursor.execute(sql_get_data_listroom,val_get_data_listroom,)
    result_get_data_listroom=mycursor.fetchall()
    print("result_get_data_listroom", result_get_data_listroom)
    if result_get_data_listroom:
        return render_template("user/listroom.html", data=result_get_data_listroom)
    else:
        return not_found()
    
    return render_template("user/listroom.html")
   

# điều hướng tới trang đăng nhập
@app_user.route("/login.html", methods=['GET','POST'])
def login():
    mydb=connect_to_database()
    mycursor=mydb.cursor()
    if request.method=="POST":
        email_admin=request.form["email"]
        print(" email_admin"+ email_admin)
        password_admin=request.form["password"]
        sql_login="SELECT Namelogin, passwordlogin FROM adminmanager WHERE Namelogin=%s AND passwordlogin=%s"
        val_login=(email_admin,password_admin,)
        mycursor.execute(sql_login,val_login)
        result_login=mycursor.fetchone()
        print("result_login", str(result_login))
        if result_login:
            session["email"]=email_admin
            print("session",session)

            return redirect(url_for('admin.Room'))
        
    return render_template("user/login.html")

if __name__=="__main__":
    app_user.run(debug=True)


#Sử dụng strptime để chuyển đổi chuỗi ngày thành đối tượng datetime. 
#Sử dụng strftime để định dạng lại đối tượng datetime thành chuỗi mới với định dạng "%Y-%m-%d"