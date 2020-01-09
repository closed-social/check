# coding=utf-8
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['JSON_AS_ASCII'] = False

db = SQLAlchemy(app)
class Record(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    acct = db.Column(db.String(64))
    it   = db.Column(db.String(64))
    tt   = db.Column(db.DateTime) 
    
    def __init__(self, acct, it):
        self.acct = acct
        self.it   = it
        self.tt   = datetime.now()

    def __repr__(self):
        return '[%s]%s(%s)' %(self.acct, self.it, self.tt)

@app.route('/打卡/')
def root():
    return app.send_static_file('index.html')

@app.route('/打卡/api/send', methods=['POST'])
def send():
    acct = request.form.get('acct')
    it   = request.form.get('it')

    if(not (acct and it and len(acct) < 50 and len(it) < 50)):
        return '格式不正确', 422

    last = Record.query.filter_by(acct=acct,it=it).order_by(Record.tt.desc()).first()
    if(last and datetime.now() - last.tt < timedelta(hours=6)):
        return '间隔也太短了', 422

    r = Record(acct, it)
    db.session.add(r)
    db.session.commit()

    return str(Record.query.filter_by(acct=acct,it=it).count())

@app.route('/打卡/api/its')
def its():
    query = db.session.query(Record.it.distinct().label('it'))
    its = [e.it for e in query.all()]
    return {'its': its}

@app.route('/打卡/api/top3/<acct>')
def getTop3(acct):
    query = db.session.query(
            Record.it, db.func.count(Record.id).label('it')
        ).group_by(Record.it).filter_by(acct=acct).order_by(db.desc('it')).limit(3)
    its = [{'name': e[0], 'count': e[1]} for e in query.all()]
    return {'top3': its}


@app.route('/打卡/web/all')
def allRecord():
    query = Record.query
    rs = [{
            'acct': e.acct,
            'it'  : e.it,
            'date': e.tt.strftime('%Y-%m-%d %I:%M:%S %p')
        } for e in query.all()
        ]

    return render_template('all.html', rs=rs[::-1])

@app.route('/打卡/web/acct/<acct>')
def acct_page(acct):
    query = Record.query.filter_by(acct=acct)
    rs = [{
            'it'  : e.it,
            'date': e.tt.strftime('%Y-%m-%d %I:%M:%S %p')
        } for e in query.all()
        ]
    
    return render_template('acct.html', acct=acct,rs=rs[::-1])

if __name__ == '__main__':
    app.run()
