from flask import Flask, request, current_app, jsonify
import sqlite3

def db_query():
    id = request.args.get('id', "")
    if id:
        con = sqlite3.connect(current_app.config['DB_FILE'])
        con.row_factory = sqlite3.Row
        with con:
            cur = con.execute("select * from fixes where id = ?", [id])
            d = cur.fetchone()
            res = dict(d) if d else None
    else:
        res = None

    return jsonify(res)


def create_app():
    app = Flask('liveogn')
    app.config.from_envvar("LIVEOGN_SETTINGS")

    app.add_url_rule("/", view_func=db_query, methods=['GET'])
    return app
