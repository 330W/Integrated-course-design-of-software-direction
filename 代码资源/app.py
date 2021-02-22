# -*- coding: utf-8 -*-
from datetime import datetime

from flask import Flask, render_template, request, flash, url_for, redirect
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms.fields import *
from wtforms.validators import DataRequired, Length
import numpy as np

from dbSqlite3 import *

app = Flask(__name__)
app.secret_key = 'dev'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'

# set default button sytle and size, will be overwritten by macro parameters
app.config['BOOTSTRAP_BTN_STYLE'] = 'primary'
app.config['BOOTSTRAP_BTN_SIZE'] = 'sm'

bootstrap = Bootstrap(app)

db = SQLAlchemy(app)


#登陆界面设计
class HelloForm(FlaskForm):
    username = StringField(u'用户名', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField(u'密码', validators=[Length(0, 10)])
    select = SelectField(u'身份', choices=[('student', 'Student'), ('teacher', 'Teacher')])
    submit = SubmitField(u'登录')


class AccountForm(FlaskForm):

    secret = PasswordField(u'旧密码', validators=[DataRequired(), Length(0, 10)], render_kw={'placeholder': '旧密码'})
    password = PasswordField(u'新密码', validators=[DataRequired(), Length(0, 10)], render_kw={'placeholder': '新密码'})
    submit = SubmitField(u'修改密码')


class SelectForm(FlaskForm):
    title = StringField(u'课程代码', render_kw={'placeholder': '课程代码'})
    submit = SubmitField(u'选课')


class DeleteForm(FlaskForm):
    title = StringField(u'课程代码', render_kw={'placeholder': '课程代码'})
    submit = SubmitField(u'退课')


class ScoreForm(FlaskForm):
    title_sno = StringField(u'学号', render_kw={'placeholder': '学号'})
    title_cno = StringField(u'课程号', render_kw={'placeholder': '课程号'})
    title_score = StringField(u'分数', render_kw={'placeholder': '分数'})
    submit = SubmitField(u'录入')

class SortForm(FlaskForm):
    title_keda = StringField(u'课程号', render_kw={'placeholder': '课程号'})
    submit22 = SubmitField(u'成绩排序')

#调课界面设计
class ChangeForm(FlaskForm):
    title_cno = StringField(u'课程号', render_kw={'placeholder': '课程号'})
    select1 = SelectField(u'星期几', choices=[('星期一', '星期一'), ('星期二', '星期二'), ('星期三', '星期三'), ('星期四', '星期四'), ('星期五', '星期五'), ('星期六', '星期六'), ('星期日', '星期日')])
    select2 = SelectField(u'时间段',choices=[('8:15~10:05', '8:15~10:05'), ('10:25~12:00', '10:25~12:00'), ('15:00~13:35', '15:00~13:35'), ('18:00~20:25', '18:00~20:25')])

    submit = SubmitField(u'调课')

class AllsortForm(FlaskForm):
    select = SelectField(u'班别',
                          choices=[('整个专业', '整个专业'),  ('计科181', '计科181'),('计科182', '计科182'), ('计科183', '计科183'), ('计科184', '计科184'), ('计科185', '计科185'),
                                   ('计科186', '计科186'),('返回', '返回')])
    submit = SubmitField(u'成绩排序')
# 登录页
@app.route('/', methods=['GET', 'POST'])
def index():
    form = HelloForm()
    if request.method == "GET":
        return render_template('index.html', form=form)

    if form.validate_on_submit():
        if form.select.data == 'student':
            result, _ = GetSql2("select * from student where sno='%s'" % form.username.data)
            if not result:
                flash(u'用户名不存在', 'warning')
                return render_template('index.html', form=form)

            if result[0][5] == form.password.data:
                return render_template('student.html', sno=form.username.data)
            else:
                flash(u'密码错误', 'warning')
                return render_template('index.html', form=form)

        if form.select.data == 'teacher':
            result, _ = GetSql2("select * from teacher where tno='%s'" % form.username.data)
            if not result:
                flash(u'用户名不存在', 'warning')
                return render_template('index.html', form=form)

            if result[0][2] == form.password.data:
                if result[0][4] == 1:
                    return render_template('head_teacher.html', tno=form.username.data)
                else:
                    return render_template('teacher.html', tno=form.username.data)
            else:
                flash(u'密码错误', 'warning')
                return render_template('index.html', form=form)


# 学生主页
@app.route('/student/<int:sno>', methods=['GET', 'POST'])
def student(sno):
    return render_template('student.html', sno=sno)


# 基本信息查看、学生个人登录密码修改功能
@app.route('/student/<int:sno>/account', methods=['GET', 'POST'])
def student_account(sno):
    form = AccountForm()

    result, _ = GetSql2("select * from student where sno='%s'" % sno)
    name = result[0][1]
    gender = result[0][2]
    birthday = result[0][3]
    birthtime = birthday
    major = result[0][4]
    classno = result[0][6]

    result2, _ = GetSql2("select * from classes where classno='%s'" % classno)
    classes = result2[0][1]
    tno = result2[0][2]

    result3, _ = GetSql2("select * from teacher where tno='%s'" % tno)
    tea_name = result3[0][1]

    if form.validate_on_submit():
        result, _ = GetSql2("select * from student where sno='%s'" % sno)
        if form.secret.data == result[0][5]:
            data = dict(
                sno=sno,
                name=name,
                gender=gender,
                birthday=birthday,
                major=major,
                password=form.password.data,
                classno = classno,
            )
            UpdateData(data, "student")
            flash(u'修改成功！', 'success')
        else:
            flash(u'原密码错误', 'warning')

    return render_template('student_account.html', sno=sno, name=name, gender=gender, birthday=birthtime,
                           major=major,classes = classes,tea_name = tea_name, form=form)


# 学生查看课表安排（开设课程基本信息、开设课程学生名单）
@app.route('/student/<int:sno>/course_table', methods=['GET', 'POST'])
def student_course_table(sno):

    messages=[[],[],[],[],  [],[],[],[],  [],[],[],[],  [],[],[],[],  [],[],[],[] ,  [],[],[],[] ,  [],[],[],[]]
    result_score, _ = GetSql2("select * from score where sno='%s'" % sno)
    result_student, _ = GetSql2("select * from student where sno='%s'" % sno)
    name = result_student[0][1]

    for i in result_score:
        result_course, _ = GetSql2("select * from course where cno='%s'" % i[1])
        result_teacher = GetSql2("select * from teacher where tno='%s'" % result_course[0][2])
        result_group = GetSql2("select * from groups  where gno='%s'" % result_course[0][3])

        message =[]
        time = result_course[0][4].split('/')[0]
        strs = result_course[0][1]
        message.append(strs)
        strs = time + '/' + result_course[0][6] + '/' + result_teacher[0][0][1] + '/' + result_group[0][0][
            3] + '/总学时:' + str(
            result_group[0][0][4]) + '/学分:' + str(result_group[0][0][5])
        message.append(strs)

        dijijie = result_course[0][4].split('/')[2]
        week = result_course[0][4].split('/')[1]
        num = 0
        if week == '星期一': num = 0
        elif week == '星期二': num = 1
        elif week == '星期三': num = 2
        elif week == '星期四': num = 3
        elif week == '星期五': num = 4
        elif week == '星期六': num = 5
        elif week == '星期日': num = 6

        if dijijie =='8:15~10:05' : num = num*4 +0
        elif dijijie == '10:25~12:00': num = num * 4 + 1
        elif dijijie == '15:00~16:35': num = num * 4 + 2
        elif dijijie == '18:00~20:25': num = num * 4 + 3

        messages[num].append(message)

        import time
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        day = now[:10].split('-')[2]
        kaoshi = 20 - int(day)

    return render_template('student_course_table.html', sno=sno,messages=messages,name= name,kaoshi =kaoshi)


# 学生选课功能
@app.route('/student/<int:sno>/course_select', methods=['GET', 'POST'])
def student_course_select(sno):
    form = SelectForm()

    result_student, _ = GetSql2("select * from student where sno='%s'" % sno)
    classno = result_student[0][6]

    result_course_class, _ = GetSql2("select * from class_course where classno='%s'" % classno)

    messages = []
    message1=[]
    message2 =[]
    for i in result_course_class:
        result_course, _ = GetSql2("select * from course where cno='%s'" % i[0] )
        result_teacher = GetSql2("select * from teacher where tno='%s'" % result_course[0][2])
        result_score = GetSql2("select count(*) from score where cno='%s'" % i[0])
        result_group = GetSql2("select * from groups  where gno='%s'" % result_course[0][3])
        message = {'category':result_group[0][0][2],'grade':result_group[0][0][5],  'gno': result_course[0][3], 'name': result_course[0][1], 'tname': result_teacher[0][0][1], 'count': result_score[0][0][0],'time':result_course[0][4]}
        if result_group[0][0][2] == '专业必修课程':
            message1.append(message)
        else :message2.append(message)

    messages.append(message1)
    messages.append(message2)
    titles = [('gno', '课程代码'), ('name', '课程名'), ('tname', '任课教师'),('grade','学分'),('time','上课时间'),('count', '已选课人数')]

    if form.validate_on_submit():
        if not form.title.data:
            flash(u'请填写课程代码', 'warning')
        else:
            result =[]
            for i in result_course_class:
                result_course, _ = GetSql2("select * from course where cno='%s'" % i[0])
                if int(result_course[0][3]) == int(form.title.data):
                    result.append(result_course[0][0])
                    break

            #result, _ = GetSql2("select * from course where cno='%s'" % form.title.data)
            if not result:
                flash(u'课程不存在', 'warning')
            else:
                result1 = result[0]
                result, _ = GetSql2("select * from score where sno='%s' and cno='%s'" % (sno, result[0]))
                if result:
                    flash(u'课程选过了', 'warning')
                else:
                    data = dict(
                        sno=sno,
                        cno=result1
                    )
                    InsertData(data, "score")
                    flash('选课成功', 'success')
                    messages = []
                    message1 = []
                    message2 = []
                    for i in result_course_class:
                        result_course, _ = GetSql2("select * from course where cno='%s'" % i[0])
                        result_teacher = GetSql2("select * from teacher where tno='%s'" % result_course[0][2])
                        result_score = GetSql2("select count(*) from score where cno='%s'" % i[0])
                        result_group = GetSql2("select * from groups  where gno='%s'" % result_course[0][3])
                        message = {'category': result_group[0][0][2], 'grade': result_group[0][0][5],
                                   'gno': result_course[0][3], 'name': result_course[0][1],
                                   'tname': result_teacher[0][0][1], 'count': result_score[0][0][0],
                                   'time': result_course[0][4]}
                        if result_group[0][0][2] == '专业必修课程':
                            message1.append(message)
                        else:
                            message2.append(message)

                    messages.append(message1)
                    messages.append(message2)

    return render_template('student_course_select.html', sno=sno, messages=messages, titles=titles, form=form)


# 学生退课功能
@app.route('/student/<int:sno>/course_delete', methods=['GET', 'POST'])
def student_course_delete(sno):
    form = DeleteForm()

    result_score, _ = GetSql2("select * from score where sno='%s'" % sno)
    messages = []
    for i in result_score:
        result_course, _ = GetSql2("select * from course where cno='%s'" % i[1])
        result_teacher, _ = GetSql2("select * from teacher where tno='%s'" % result_course[0][2])
        result_group = GetSql2("select * from groups  where gno='%s'" % result_course[0][3])

        message = {'category': result_group[0][0][2],'method': result_group[0][0][3], 'grade': result_group[0][0][5], 'gno': result_course[0][3],
                   'name': result_course[0][1], 'tname': result_teacher[0][1],'time': result_course[0][4]}
        messages.append(message)

    titles = [('gno', '课程代码'), ('name', '课程名'), ('tname', '任课教师'),('grade','学分'),('category', '课程性质'),('method','考察方式')]

    result_student, _ = GetSql2("select * from student where sno='%s'" % sno)
    classno = result_student[0][6]
    result_course_class, _ = GetSql2("select * from class_course where classno='%s'" % classno)
    if form.validate_on_submit():
        if not form.title.data:
            flash(u'请填写课程号', 'warning')
        else:
            result = []
            for i in result_course_class:
                result_course, _ = GetSql2("select * from course where cno='%s'" % i[0])
                if int(result_course[0][3]) == int(form.title.data):
                    result.append(result_course[0][0])
                    break

            if not result:
                flash(u'课程不存在', 'warning')
            else:
                result_group, _ = GetSql2("select * from groups where gno='%s'" % form.title.data)

                if result_group[0][2] == '专业必修课程':
                    flash(u'必修课程不可退！', 'warning')
                else:
                    DelDataById('sno', 'cno', sno, result[0], "score")
                    flash('退课成功', 'success')
                    return redirect(url_for('student_course_delete', sno=sno, messages=messages, titles=titles,
                                            form=form))

    return render_template('student_course_delete.html', sno=sno, messages=messages, titles=titles, form=form)


# 学生成绩查询功能
@app.route('/student/<int:sno>/score', methods=['GET', 'POST'])
def student_score(sno):
    result_score, _ = GetSql2("select * from score where sno='%s'" % sno)

    all_jidian = 0
    all_xuefen = 0
    messages = []
    for i in result_score:
        result_course, _ = GetSql2("select * from course where cno='%s'" % i[1])
        result_teacher, _ = GetSql2("select * from teacher where tno='%s'" % result_course[0][2])
        result_group = GetSql2("select * from groups  where gno='%s'" % result_course[0][3])
        jidian = 0

        if not i[2]:
            message = {'gno': result_course[0][3], 'cname': result_course[0][1], 'tname': result_teacher[0][1], 'score': '无成绩','jidian':'无绩点'}
        else:
            if i[2]<60:
                jidian = 1
            else :
                jidian = (i[2]-60)/10 + 1
                if jidian>=4:
                    jidian =4
            all_xuefen += result_group[0][0][5]
            all_jidian += result_group[0][0][5] * jidian

            message = {'gno': result_course[0][3], 'cname': result_course[0][1], 'tname': result_teacher[0][1], 'score': i[2],'jidian':jidian}
        messages.append(message)

    titles = [('gno', '已选课程号'), ('cname', '课程名'), ('tname', '任课教师'), ('score', '成绩'), ('jidian', '绩点')]
    all_jidian = all_jidian /all_xuefen
    return render_template('student_score.html', sno=sno, messages=messages, titles=titles, all_jidian=round(all_jidian,2))


# 老师主页
@app.route('/teacher/<int:tno>', methods=['GET', 'POST'])
def teacher(tno):
    return render_template('teacher.html', tno=tno)


# 老师个人登录密码修改功能
@app.route('/teacher/<int:tno>/account', methods=['GET', 'POST'])
def teacher_account(tno):
    form = AccountForm()

    result, _ = GetSql2("select * from teacher where tno='%s'" % tno)
    name = result[0][1]
    gender = result[0][3]
    head= result[0][4]
    str = '任课教师'
    if head:
        str = "教导主任"
    if form.is_submitted():
        result, _ = GetSql2("select * from teacher where tno='%s'" % tno)
        if form.secret.data == result[0][2]:
            data = dict(
                tno=tno,
                name=result[0][1],
                password=form.password.data,
                gender = gender,
                head = head
            )
            UpdateData(data, "teacher")
            flash(u'修改成功！', 'success')
        else:
            flash(u'原密码错误', 'warning')

    return render_template('teacher_account.html', tno=tno, name=name ,str = str,gender = gender,form=form)

# 老师开课信息查看（开设课程基本信息、开设课程学生名单）
@app.route('/teacher/<int:tno>/course', methods=['GET', 'POST'])
def teacher_course(tno):
    form =  ChangeForm()
    result_course, _ = GetSql2("SELECT * FROM course WHERE tno='%s'" % tno)

    classe = []
    messages = []
    for i in result_course:
        result_group, _ = GetSql2("SELECT * FROM groups WHERE gno='%s'" % i[3])

        row = {'cno': i[0],'gno': result_group[0][0], 'name': result_group[0][1], 'category': result_group[0][2], 'method': result_group[0][3],
               'keshi': result_group[0][4], 'xuefen': result_group[0][5], 'time': i[4],'banji':i[5],'station':i[6]}
        classe.append(row)


        message = []
        result_score, _ = GetSql2("SELECT sno FROM score WHERE cno='%s'" % i[0])
        if not result_score:
            continue
        else:
            for j in result_score:
                result_student, _ = GetSql2("select * from student where sno='%s'" % j[0])
                classno = result_student[0][6]

                result2, _ = GetSql2("select * from classes where classno='%s'" % classno)
                classes = result2[0][1]
                row = {'cno': i[0], 'cname': i[1], 'sno': result_student[0][0], 'name': result_student[0][1],
                       'gender': result_student[0][2], 'major': result_student[0][4],'classes':classes }
                message.append(row)
        messages.append(message)


    titles = [('sno', '学号'), ('name', '姓名'), ('gender', '性别'), ('classes', '班别')]
    title = [('cno','课程号'),('gno', '课程代码'), ('name', '课程名'), ('banji', '上课班级'), ('station', '上课地点'),('time', '上课时间')]

    if form.validate_on_submit():
        if not form.title_cno.data:
            flash(u'请填写课程号', 'warning')
        else:
            target_course, _ = GetSql2("select * from course where cno='%s' and tno='%s'" % (form.title_cno.data ,tno) )
            if not target_course:
                flash(u'课程不存在', 'warning')
            else:
                result_course, _ = GetSql2("select * from course")
                flag = 1
                for i in result_course:
                    time = i[4]
                    time = time.split('/')
                    if form.select1.data==time[1] and form.select2.data==time[2]:
                        flag = 0
                        break

                if flag:
                    data = dict(
                        cno=target_course[0][0],
                        name=target_course[0][1],
                        tno=target_course[0][2] ,
                        gno = target_course[0][3],
                        course_time =time[0]+'/'+form.select1.data + '/'+form.select2.data,
                        tea_class =target_course[0][5] ,
                        station =target_course[0][6]
                    )
                    UpdateData(data, "course")
                    flash('调课成功', 'success')
                    classe = []
                    result_course, _ = GetSql2("SELECT * FROM course WHERE tno='%s'" % tno)
                    for i in result_course:
                        result_group, _ = GetSql2("SELECT * FROM groups WHERE gno='%s'" % i[3])

                        row = {'cno': i[0], 'gno': result_group[0][0], 'name': result_group[0][1],
                               'category': result_group[0][2], 'method': result_group[0][3],
                               'keshi': result_group[0][4], 'xuefen': result_group[0][5], 'time': i[4], 'banji': i[5],
                               'station': i[6]}
                        classe.append(row)
                    return render_template('teacher_course.html', form=form, tno=tno, messages=messages, titles=titles,
                                           classe=classe, title=title)

                else:
                    flash(u'时间冲突!请重新选择调课时间', 'warning')

    return render_template('teacher_course.html', form=form ,tno=tno, messages=messages, titles=titles,classe = classe,title= title)


# 老师成绩录入和修改功能
@app.route('/teacher/<int:tno>/score', methods=['GET', 'POST'])
def teacher_score(tno):
    form = ScoreForm()
    form2 = SortForm()
    result_course, _ = GetSql2("SELECT * FROM course WHERE tno='%s'" % tno)

    messages = []
    for i in result_course:
        message = []
        result_score, _ = GetSql2("SELECT * FROM score WHERE cno='%s'" % i[0])
        for j in result_score:
            result_student, _ = GetSql2("select * from student where sno='%s'" % j[0])
            classno = result_student[0][6]

            result2, _ = GetSql2("select * from classes where classno='%s'" % classno)
            classes = result2[0][1]

            jidian = 0

            if not j[2]:
                row = {'cname': i[1], 'cno': i[0], 'sno': j[0], 'name': result_student[0][1], 'classes':classes,
                           'score': '无成绩', 'jidian': '无绩点'}
            else:
                if j[2] < 60:
                    jidian = 1
                else:
                    jidian = (j[2] - 60) / 10 + 1
                    if jidian >= 4:
                        jidian = 4
                row = {'cname': i[1], 'cno': i[0], 'sno': j[0], 'name': result_student[0][1], 'score': j[2],'classes':classes,'jidian': jidian}
            message.append(row)
        if not message:
            continue
        messages.append(message)

    titles = [('sno', '学号'), ('name', '姓名'), ('classes', '班别'),('score', '成绩'),('jidian','绩点')]
    if form.validate_on_submit():
        if form.submit.data:
            if not (form.title_cno.data and form.title_sno.data and form.title_score.data):
                flash(u'输入不完整', 'warning')
            else:
                result, _ = GetSql2(
                    "select * from score where cno='%s' and sno='%s'" % (form.title_cno.data, form.title_sno.data))
                if result:
                    data = dict(
                        sno=form.title_sno.data,
                        cno=form.title_cno.data,
                        score=form.title_score.data
                    )
                    UpdateData(data, "score")
                    flash(u'录入成功！', 'success')
                    return redirect(url_for('teacher_score', tno=tno, messages=messages, titles=titles, form=form))
                else:
                    flash(u'该学生未选课', 'warning')

    if form2.validate_on_submit():
        if form2.submit22.data:
            if not (form2.title_keda.data):
                flash(u'请输入课程号', 'warning')
            else:
                target = []
                start = 0
                for i in messages:
                    if int(i[0]['cno'])== int(form2.title_keda.data):
                        target = i
                        break
                    start+=1
                if not target:
                    flash(u'课程不存在', 'warning')
                else:
                    flash(u'排序成功', 'success')

                    for kkk in i:
                        if kkk['score'] == '无成绩':kkk['score'] = 0
                    sort_grade = sorted(i, key=lambda j: (j['sno']))
                    sort_grade = sorted(sort_grade, key=lambda j: (j['score']), reverse=True)
                    for kkk in sort_grade:
                        if kkk['score'] == 0:kkk['score'] = '无成绩'
                    messages[start] = sort_grade
                    return render_template('teacher_score.html', tno=tno, messages=messages, titles=titles, form=form,
                                       form2=form2)

    return render_template('teacher_score.html', tno=tno, messages=messages, titles=titles, form=form ,form2=form2)




# 教导主任主页
@app.route('/head_teacher/<int:tno>', methods=['GET', 'POST'])
def head_teacher(tno):
    return render_template('head_teacher.html', tno=tno)


# 教导主任主页个人登录密码修改功能
@app.route('/head_teacher/<int:tno>/account', methods=['GET', 'POST'])
def head_teacher_account(tno):
    form = AccountForm()

    result, _ = GetSql2("select * from teacher where tno='%s'" % tno)
    name = result[0][1]
    gender = result[0][3]
    head= result[0][4]
    str = '任课教师'
    if head:
        str = "系主任"
    if form.is_submitted():
        result, _ = GetSql2("select * from teacher where tno='%s'" % tno)
        if form.secret.data == result[0][2]:
            data = dict(
                tno=tno,
                name=result[0][1],
                password=form.password.data,
                gender = gender,
                head = head
            )
            UpdateData(data, "teacher")
            flash(u'修改成功！', 'success')
        else:
            flash(u'原密码错误', 'warning')

    return render_template('head_teacher_account.html', tno=tno, name=name ,str = str,gender = gender,form=form)

# 教导主任主页开课信息查看（开设课程基本信息、开设课程学生名单）
@app.route('/head_teacher/<int:tno>/course', methods=['GET', 'POST'])
def head_teacher_course(tno):
    form = ChangeForm()
    result_course, _ = GetSql2("SELECT * FROM course WHERE tno='%s'" % tno)

    classe = []
    messages = []
    for i in result_course:
        result_group, _ = GetSql2("SELECT * FROM groups WHERE gno='%s'" % i[3])

        row = {'cno': i[0], 'gno': result_group[0][0], 'name': result_group[0][1], 'category': result_group[0][2],
               'method': result_group[0][3],
               'keshi': result_group[0][4], 'xuefen': result_group[0][5], 'time': i[4], 'banji': i[5],
               'station': i[6]}
        classe.append(row)

        message = []
        result_score, _ = GetSql2("SELECT sno FROM score WHERE cno='%s'" % i[0])
        if not result_score:
            continue
        else:
            for j in result_score:
                result_student, _ = GetSql2("select * from student where sno='%s'" % j[0])
                classno = result_student[0][6]

                result2, _ = GetSql2("select * from classes where classno='%s'" % classno)
                classes = result2[0][1]
                row = {'cno': i[0], 'cname': i[1], 'sno': result_student[0][0], 'name': result_student[0][1],
                       'gender': result_student[0][2], 'major': result_student[0][4], 'classes': classes}
                message.append(row)
        messages.append(message)

    titles = [('sno', '学号'), ('name', '姓名'), ('gender', '性别'), ('classes', '班别')]
    title = [('cno', '课程号'), ('gno', '课程代码'), ('name', '课程名'), ('banji', '上课班级'), ('station', '上课地点'),
             ('time', '上课时间')]

    if form.validate_on_submit():
        if not form.title_cno.data:
            flash(u'请填写课程号', 'warning')
        else:
            target_course, _ = GetSql2(
                "select * from course where cno='%s' and tno='%s'" % (form.title_cno.data, tno))
            if not target_course:
                flash(u'课程不存在', 'warning')
            else:
                result_course, _ = GetSql2("select * from course")
                flag = 1
                for i in result_course:
                    time = i[4]
                    time = time.split('/')
                    if form.select1.data == time[1] and form.select2.data == time[2]:
                        flag = 0
                        break

                if flag:
                    data = dict(
                        cno=target_course[0][0],
                        name=target_course[0][1],
                        tno=target_course[0][2],
                        gno=target_course[0][3],
                        course_time=time[0] + '/' + form.select1.data + '/' + form.select2.data,
                        tea_class=target_course[0][5],
                        station=target_course[0][6]
                    )
                    UpdateData(data, "course")
                    flash('调课成功', 'success')
                    classe = []
                    result_course, _ = GetSql2("SELECT * FROM course WHERE tno='%s'" % tno)
                    for i in result_course:
                        result_group, _ = GetSql2("SELECT * FROM groups WHERE gno='%s'" % i[3])

                        row = {'cno': i[0], 'gno': result_group[0][0], 'name': result_group[0][1],
                               'category': result_group[0][2], 'method': result_group[0][3],
                               'keshi': result_group[0][4], 'xuefen': result_group[0][5], 'time': i[4],
                               'banji': i[5],
                               'station': i[6]}
                        classe.append(row)
                    return render_template('teacher_course.html', form=form, tno=tno, messages=messages,
                                           titles=titles,
                                           classe=classe, title=title)

                else:
                    flash(u'时间冲突!请重新选择调课时间', 'warning')

    return render_template('head_teacher_course.html', form=form, tno=tno, messages=messages, titles=titles,
                           classe=classe, title=title)


# 教导主任主页查看所有学生（学生名单）
@app.route('/head_teacher/<int:tno>/student', methods=['GET', 'POST'])
def head_teacher_all_student(tno):
    form = AllsortForm()
    messages = []

    result_classes, _ = GetSql2("select * from classes ")

    for j in result_classes:
        message = []
        result_student, _ = GetSql2("select * from student WHERE classno='%s'" % j[0] )
        counts = GetSql2("select count(*) from student where classno='%s'" % j[0])
        for i in result_student:
            result2, _ = GetSql2("select * from classes where classno='%s'" % i[6])

            classes = result2[0][1]
            kno = result2[0][2]

            result3, _ = GetSql2("select * from teacher where tno='%s'" % kno)

            tea_name = result3[0][1]

            result4, _ = GetSql2("select * from score where sno='%s'" %  i[0])

            all_xuefen = 0
            mean_jidian = 0
            for jjj in result4:
                result_course, _ = GetSql2("select * from course where cno='%s'" % jjj[1])
                result_group , _ = GetSql2("select * from groups where gno='%s'" % result_course[0][3])
                xuefen = result_group[0][5]
                score = jjj[2]
                if not score:
                    continue
                else:
                    if score < 60:
                        jidian = 1
                    else:
                        jidian = (score - 60) / 10 + 1
                        if jidian >= 4:
                            jidian = 4
                    mean_jidian += jidian * xuefen
                    all_xuefen+= xuefen
            mean_jidian = mean_jidian/all_xuefen
            row = {'sno': i[0], 'name': i[1], 'gender': i[2], 'birthday': i[3],
                   'major': i[4], 'classes': '班级:'+classes, 'tea_name':'班主任:'+tea_name,'counts':'总人数:'+str(counts[0][0][0]),'jidian':round(mean_jidian,2)}
            message.append(row)
        messages.append(message)
    titles = [('sno', '学号'), ('name', '姓名'), ('gender', '性别'), ('jidian', '平均绩点'), ('birthday', '入学日期')]

    old_messages = messages
    if form.validate_on_submit():
        sort_grade =[]
        titles = [('sno', '学号'), ('name', '姓名'), ('gender', '性别'), ('jidian', '平均绩点'), ('birthday', '入学日期')]
        if form.select.data == '返回':
            return render_template('head_teacher_all_student.html', form=form, tno=tno, messages=old_messages,
                                   titles=titles)
        titles = [('index','排名'),('sno', '学号'), ('name', '姓名'), ('gender', '性别'), ('jidian', '平均绩点')]
        if form.select.data == '计科181':
            sort_grade = sorted(messages[0], key=lambda j: (j['sno']))
            sort_grade = sorted(sort_grade, key=lambda j: (j['jidian']), reverse=True)
        elif form.select.data == '计科182':
            sort_grade = sorted(messages[1], key=lambda j: (j['sno']))
            sort_grade = sorted(sort_grade, key=lambda j: (j['jidian']), reverse=True)
        elif form.select.data == '计科183':
            sort_grade = sorted(messages[2], key=lambda j: (j['sno']))
            sort_grade = sorted(sort_grade, key=lambda j: (j['jidian']), reverse=True)
        elif form.select.data == '计科184':
            sort_grade = sorted(messages[3], key=lambda j: (j['sno']))
            sort_grade = sorted(sort_grade, key=lambda j: (j['jidian']), reverse=True)
        elif form.select.data == '计科185':
            sort_grade = sorted(messages[4], key=lambda j: (j['sno']))
            sort_grade = sorted(sort_grade, key=lambda j: (j['jidian']), reverse=True)
        elif form.select.data == '计科186':
            sort_grade = sorted(messages[5], key=lambda j: (j['sno']))
            sort_grade = sorted(sort_grade, key=lambda j: (j['jidian']), reverse=True)
        else:
            for mes in messages:
                for me in mes:
                    print(me)
                    row = {'sno': me['sno'], 'name': me['name'], 'gender': me['gender'], 'birthday': me['birthday'],
                           'class': me['classes'].split(':')[1], 'classes': '本专业总排名', 'tea_name': ' ', 'counts': ' ',
                           'jidian': me['jidian']}
                    sort_grade.append(row)
            sort_grade = sorted(sort_grade, key=lambda j: (j['sno']))
            sort_grade = sorted(sort_grade, key=lambda j: (j['jidian']), reverse=True)
            titles = [('index','排名'),('sno', '学号'), ('name', '姓名'), ('gender', '性别'),('class','班别'), ('jidian', '平均绩点')]
        messages = []
        num =1
        for kk in sort_grade:
            kk['index'] = num
            num+=1
        messages.append(sort_grade)
        return render_template('head_teacher_all_student.html', form=form, tno=tno, messages=messages, titles=titles)

    return render_template('head_teacher_all_student.html',form=form, tno=tno, messages=messages, titles=titles)

# 教导主任主页查看所有老师（老师名单）
@app.route('/head_teacher/<int:tno>/all_teacher', methods=['GET', 'POST'])
def head_teacher_all_teacher(tno):
    result_teacher, _ = GetSql2("select * from teacher ")
    messages_teacher = []
    for i in result_teacher:
        result_course_num = GetSql2("select count(*) from course where tno = '%s' " % i[0])
        row = {'tno': i[0], 'name': i[1], 'gender': i[3],'xueyuan':'计算机科学与网络工程学院','num':result_course_num[0][0][0]}
        messages_teacher.append(row)
    title1 = [('tno', '教师号'), ('name', '姓名'), ('gender', '性别'), ('xueyuan', '所属学院'), ('num', '负责课程数目')]

    return render_template('head_teacher_all_teacher.html', title1=title1,messages_teacher=messages_teacher, tno=tno)


# 教导主任主页查看所有课程（课程名单）
@app.route('/head_teacher/<int:tno>/all_course', methods=['GET', 'POST'])
def head_teacher_all_course(tno):
    result_group, _ = GetSql2("select * from groups ")
    messages_course = []
    for i in result_group:
        message=[]
        result_course, _ = GetSql2("select * from course where gno = '%s' " % i[0])
        for j in result_course:

            result_teacher, _ = GetSql2("select * from teacher where tno = '%s' " % j[2])
            result_group_teacher, _ = GetSql2("select * from group_teacher where tno = '%s' and gno ='%s' " % (j[2],i[0]))
            zhiwu = '无'
            if result_group_teacher[0][2] == 1:
                zhiwu = '课程组组长'

            row = {'gno': i[0], 'name': i[1], 'xingzhi': i[2],'keshi':i[4],'xuefen':i[5],'cno':j[0],'tea':result_teacher[0][1],'banji':j[5],'sta':j[6],'time':j[4],'zhiwu':zhiwu}
            message.append(row)

        messages_course.append(message)

    title1 = [('cno', '课程号'), ('tea', '任课教师'), ('banji', '授课班级'), ('sta', '上课地点'),('time', '上课时间'),('zhiwu', '职务')]

    return render_template('head_teacher_all_course.html', title1=title1,messages_course=messages_course, tno=tno)


# 教导主任主页成绩录入和修改功能
@app.route('/head_teacher/<int:tno>/score', methods=['GET', 'POST'])
def head_teacher_score(tno):
    form = ScoreForm()
    form2 = SortForm()
    result_course, _ = GetSql2("SELECT * FROM course WHERE tno='%s'" % tno)

    messages = []
    for i in result_course:
        message = []
        result_score, _ = GetSql2("SELECT * FROM score WHERE cno='%s'" % i[0])
        for j in result_score:
            result_student, _ = GetSql2("select * from student where sno='%s'" % j[0])
            classno = result_student[0][6]

            result2, _ = GetSql2("select * from classes where classno='%s'" % classno)
            classes = result2[0][1]

            jidian = 0

            if not j[2]:
                row = {'cname': i[1], 'cno': i[0], 'sno': j[0], 'name': result_student[0][1], 'classes': classes,
                       'score': '无成绩', 'jidian': '无绩点'}
            else:
                if j[2] < 60:
                    jidian = 1
                else:
                    jidian = (j[2] - 60) / 10 + 1
                    if jidian >= 4:
                        jidian = 4
                row = {'cname': i[1], 'cno': i[0], 'sno': j[0], 'name': result_student[0][1], 'score': j[2],
                       'classes': classes, 'jidian': jidian}
            message.append(row)
        if not message:
            continue
        messages.append(message)

    titles = [('sno', '学号'), ('name', '姓名'), ('classes', '班别'), ('score', '成绩'), ('jidian', '绩点')]
    if form.validate_on_submit():
        if form.submit.data:
            if not (form.title_cno.data and form.title_sno.data and form.title_score.data):
                flash(u'输入不完整', 'warning')
            else:
                result, _ = GetSql2(
                    "select * from score where cno='%s' and sno='%s'" % (form.title_cno.data, form.title_sno.data))
                if result:
                    data = dict(
                        sno=form.title_sno.data,
                        cno=form.title_cno.data,
                        score=form.title_score.data
                    )
                    UpdateData(data, "score")
                    flash(u'录入成功！', 'success')
                    return redirect(url_for('teacher_score', tno=tno, messages=messages, titles=titles, form=form))
                else:
                    flash(u'该学生未选课', 'warning')

    if form2.validate_on_submit():
        if form2.submit22.data:
            if not (form2.title_keda.data):
                flash(u'请输入课程号', 'warning')
            else:
                target = []
                start = 0
                for i in messages:
                    if int(i[0]['cno']) == int(form2.title_keda.data):
                        target = i
                        break
                    start += 1
                if not target:
                    flash(u'课程不存在', 'warning')
                else:
                    flash(u'排序成功', 'success')

                    for kkk in i:
                        if kkk['score'] == '无成绩': kkk['score'] = 0

                    sort_grade = sorted(i, key=lambda j: (j['sno']))
                    sort_grade = sorted(sort_grade, key=lambda j: (j['score']), reverse=True)

                    for kkk in sort_grade:
                        if kkk['score'] == 0: kkk['score'] = '无成绩'
                    messages[start] = sort_grade
                    return render_template('teacher_score.html', tno=tno, messages=messages, titles=titles, form=form,
                                           form2=form2)

    return render_template('head_teacher_score.html', tno=tno, messages=messages, titles=titles, form=form,form2=form2)


# 教导主任查看课表安排（总的班级课表和所有班级课表）
@app.route('/head_teacher/<int:tno>/teacher_table', methods=['GET', 'POST'])
def head_teacher_course_table(tno):

    result_class = GetSql2("select * from classes")[0]
    nianji_messages = [] #年级课表
    all_messages=[] #各个班的课表
    names =[]

    nianji_messages =[[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                    [], [], []]
    for i in result_class:

        result_classes = GetSql2("select * from class_course where classno = '%s' "%i[0])
        messages = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                    [], [], [],i[1]]
        for j in result_classes[0]:
            result_course, _ = GetSql2("select * from course where cno='%s'" % j[0])
            result_teacher = GetSql2("select * from teacher where tno='%s'" % result_course[0][2])
            result_group = GetSql2("select * from groups  where gno='%s'" % result_course[0][3])
            message = []
            time = result_course[0][4].split('/')[0]
            strs = result_course[0][1]
            message.append(strs)
            strs = time + '/' + result_course[0][6] + '/' + result_teacher[0][0][1] +'/' + result_group[0][0][3] + '/总学时:' + str(
                result_group[0][0][4]) + '/学分:' + str(result_group[0][0][5])
            message.append(strs)

            dijijie = result_course[0][4].split('/')[2]
            week = result_course[0][4].split('/')[1]
            num = 0
            if week == '星期一':
                num = 0
            elif week == '星期二':
                num = 1
            elif week == '星期三':
                num = 2
            elif week == '星期四':
                num = 3
            elif week == '星期五':
                num = 4
            elif week == '星期六':
                num = 5
            elif week == '星期日':
                num = 6

            if dijijie == '8:15~10:05':
                num = num * 4 + 0
            elif dijijie == '10:25~12:00':
                num = num * 4 + 1
            elif dijijie == '15:00~16:35':
                num = num * 4 + 2
            elif dijijie == '18:00~20:25':
                num = num * 4 + 3

            messages[num].append(message)
            nianji_messages[num].append(message)
        all_messages.append(messages)

        import time
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        day = now[:10].split('-')[2]
        kaoshi = 20 - int(day)
    return render_template('head_teacher_course_table.html', tno=tno,all_messages=all_messages,nianji_messages=nianji_messages,kaoshi =kaoshi)



if __name__ == '__main__':
    app.run()
