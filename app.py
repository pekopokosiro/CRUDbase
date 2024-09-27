import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import pytz  # タイムゾーンのサポートを追加


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///materials.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# タイムゾーンの設定
timezone = pytz.timezone('Asia/Tokyo')

# カスタムフィルタの追加
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    if date is None:
        return ""
    if fmt is None:
        fmt = '%Y-%m-%d'
    return date.strftime(fmt)

# モデル定義
class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    supplier = db.Column(db.String(100), nullable=False)
    purchase_date = db.Column(db.Date, nullable=True)
    purchase_price = db.Column(db.Float, nullable=False, default=0.0)
    supplier_contact_or_notes = db.Column(db.String(100), nullable=True)


    def __repr__(self):
        return f'<Material {self.name}>'

class Usage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    quantity_used = db.Column(db.Integer, nullable=False)
    usage_date = db.Column(db.DateTime, default=datetime.utcnow)

    material = db.relationship('Material', backref=db.backref('usages', lazy=True))

    def __repr__(self):
        return f'<Usage {self.quantity_used} of Material ID {self.material_id}>'

# Recipeモデルの定義
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    labor_cost = db.Column(db.Float, nullable=False, default=0.0)
    listing_price = db.Column(db.Float, nullable=False, default=0.0)  # 販売価格
    total_cost = db.Column(db.Float, nullable=False, default=0.0)  # 原価合計
    profit_margin = db.Column(db.Float, nullable=False, default=0.0)  # 原価率



class RecipeMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    quantity_used = db.Column(db.Integer, nullable=False)

    recipe = db.relationship('Recipe', backref=db.backref('materials', lazy=True))
    material = db.relationship('Material', backref=db.backref('recipes', lazy=True))

migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

# 素材一覧表示
@app.route('/')
def index():
    search_query = request.args.get('search')
    if search_query:
        materials = Material.query.filter(
            db.or_(
                Material.name.contains(search_query),
                Material.category.contains(search_query),
                Material.supplier.contains(search_query)
            )
        ).all()
    else:
        materials = Material.query.all()
    
    return render_template('index.html', materials=materials)


# 新規素材追加
# 新規素材追加
@app.route('/add', methods=['GET', 'POST'])
def add_material():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        quantity = request.form['quantity']
        unit_price = request.form['unit_price']
        supplier = request.form['supplier']
        purchase_date = request.form.get('purchase_date')
        supplier_contact_or_notes = request.form.get('supplier_contact_or_notes')

        # purchase_dateが空でない場合のみ変換を行う
        if purchase_date:
            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
        else:
            purchase_date = None  # 空の場合はNoneを設定

        new_material = Material(
            name=name,
            category=category,
            quantity=quantity,
            unit_price=unit_price,
            supplier=supplier,
            purchase_date=purchase_date,  # 修正後のpurchase_date
            supplier_contact_or_notes=supplier_contact_or_notes
        )
        db.session.add(new_material)
        db.session.commit()

        return redirect(url_for('index'))
    categories = Material.query.with_entities(Material.category).distinct()
    return render_template('add_material.html', categories=categories)


# @app.route('/add', methods=['GET', 'POST'])
# def add_material():
#     if request.method == 'POST':
#         name = request.form['name']
#         category = request.form['category']
#         quantity = request.form['quantity']
#         unit_price = request.form['unit_price']
#         supplier = request.form['supplier']
#         purchase_date = request.form.get('purchase_date')
#         supplier_contact_or_notes = request.form.get('supplier_contact_or_notes')

#         if purchase_date:
#             purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()

#         new_material = Material(
#             name=name,
#             category=category,
#             quantity=quantity,
#             unit_price=unit_price,
#             supplier=supplier,
#             purchase_date=purchase_date,
#             supplier_contact_or_notes=supplier_contact_or_notes
#         )
#         db.session.add(new_material)
#         db.session.commit()

#         return redirect(url_for('index'))
#     categories = Material.query.with_entities(Material.category).distinct()
#     return render_template('add_material.html', categories=categories)

# 素材編集
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_material(id):
    material = Material.query.get_or_404(id)
    if request.method == 'POST':
        try:
            material.name = request.form['name']
            material.quantity = int(request.form['quantity'])  # 数値型への変換
            material.unit_price = float(request.form['unit_price'])  # 数値型への変換
            material.category = request.form['category']
            material.supplier = request.form['supplier']
            purchase_date = request.form.get('purchase_date')
            if purchase_date:
                material.purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
            else:
                material.purchase_date = None
            material.supplier_contact_or_notes = request.form.get('supplier_contact_or_notes')

            db.session.commit()
            return redirect(url_for('index'))
        except ValueError as ve:
            db.session.rollback()
            print(f"ValueError occurred: {ve}")
            return f"Invalid data type provided: {ve}", 400
        except Exception as e:
            db.session.rollback()
            print(f"Error occurred: {e}")
            return f"An error occurred during the update process: {e}", 400

    categories = Material.query.with_entities(Material.category).distinct()
    return render_template('edit_material.html', material=material, categories=categories)

# 素材を使用する
@app.route('/use_material/<int:id>', methods=['GET', 'POST'])
def use_material(id):
    material = Material.query.get_or_404(id)
    if request.method == 'POST':
        quantity_used = int(request.form['quantity_used'])
        if material.quantity >= quantity_used:
            material.quantity -= quantity_used
            usage = Usage(material_id=id, quantity_used=quantity_used)
            db.session.add(usage)
            db.session.commit()
            return redirect(url_for('index'))
        else:
            return f"Not enough material in stock. Available quantity: {material.quantity}", 400
    return render_template('use_material.html', material=material)


# 使用履歴一覧
@app.route('/usage_history')
def usage_history():
    usages = Usage.query.all()
    return render_template('usage_history.html', usages=usages)

# 素材削除
@app.route('/delete/<int:id>')
def delete_material(id):
    material = Material.query.get_or_404(id)
    db.session.delete(material)
    db.session.commit()
    return redirect(url_for('index'))


# @app.route('/new_recipe', methods=['GET', 'POST'])
# def new_recipe():
    if request.method == 'POST':
        try:
            # レシピ名の取得とエラーチェック
            name = request.form.get('name')
            if not name:
                return "レシピ名が必要です", 400

            description = request.form.get('description')
            labor_cost = float(request.form.get('labor_cost', 0.0))
            listing_price = float(request.form.get('listing_price', 0.0))

            # 新しいレシピを作成
            new_recipe = Recipe(name=name, description=description, labor_cost=labor_cost, listing_price=listing_price)
            db.session.add(new_recipe)
            db.session.flush()  # レシピIDを取得するためにフラッシュ

            # 素材名と使用量を取得
            material_names = request.form.getlist('material_name')
            quantities_used = request.form.getlist('quantity_used')

            if len(material_names) != len(quantities_used):
                return "素材名と使用量の数が一致しません", 400

            total_material_cost = 0  # 合計素材原価を計算するための変数
            material_entries = []

            for i in range(len(material_names)):
                material_name = material_names[i]
                quantity_used = quantities_used[i]

                if material_name and quantity_used:
                    material = Material.query.filter_by(name=material_name).first()
                    if material and int(quantity_used) <= material.quantity:
                        material.quantity -= int(quantity_used)
                        material_entry = RecipeMaterial(
                            recipe_id=new_recipe.id,
                            material_id=material.id,
                            quantity_used=int(quantity_used)
                        )
                        material_entries.append(material_entry)
                        
                        # 素材の合計原価を計算
                        total_material_cost += material.unit_price * int(quantity_used)
                    else:
                        db.session.rollback()
                        return f"{material_name}の在庫が不足しています。", 400
                else:
                    return "素材名または使用量が不正です", 400

            # 合計原価と原価率の計算
            total_cost = total_material_cost + labor_cost
            profit_margin = (total_cost / listing_price * 100) if listing_price > 0 else 0

            # 合計原価と原価率をレシピに追加
            new_recipe.total_cost = total_cost
            new_recipe.profit_margin = profit_margin

            db.session.add_all(material_entries)
            db.session.commit()

            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            return f"エラーが発生しました: {str(e)}", 500
    else:
        materials = Material.query.all()
        categories = db.session.query(Material.category).distinct().all()

        materials_data = [
            {
                "name": material.name,
                "category": material.category,
                "id": material.id,
                "quantity": material.quantity,
                "unit_price": material.unit_price,
                "supplier": material.supplier,
                "purchase_date": material.purchase_date.strftime('%Y-%m-%d') if material.purchase_date else None,
                "supplier_contact_or_notes": material.supplier_contact_or_notes
            } for material in materials
        ]

        return render_template('new.html', materials=materials_data, categories=[c[0] for c in categories])

@app.route('/new_recipe', methods=['GET', 'POST'])
def new_recipe():
    materials = Material.query.all()
    categories = db.session.query(Material.category).distinct().all()
    materials_data = [
        {
            "name": material.name,
            "category": material.category,
            "id": material.id,
            "quantity": material.quantity,
            "unit_price": material.unit_price,
            "supplier": material.supplier,
            "purchase_date": material.purchase_date.strftime('%Y-%m-%d') if material.purchase_date else None,
            "supplier_contact_or_notes": material.supplier_contact_or_notes
        } for material in materials
    ]

    if request.method == 'POST':
        try:
            # レシピ名の取得とエラーチェック
            name = request.form.get('name')
            if not name:
                return render_template('new.html', error="レシピ名が必要です", form_data=request.form, materials=materials_data, categories=[c[0] for c in categories])

            description = request.form.get('description')
            labor_cost = float(request.form.get('labor_cost', 0.0))
            listing_price = float(request.form.get('listing_price', 0.0))

            # 新しいレシピを作成
            new_recipe = Recipe(name=name, description=description, labor_cost=labor_cost, listing_price=listing_price)
            db.session.add(new_recipe)
            db.session.flush()  # レシピIDを取得するためにフラッシュ

            # 素材名と使用量を取得
            material_names = request.form.getlist('material_name')
            quantities_used = request.form.getlist('quantity_used')

            if len(material_names) != len(quantities_used):
                return render_template('new.html', error="素材名と使用量の数が一致しません", form_data=request.form, materials=materials_data, categories=[c[0] for c in categories])

            total_material_cost = 0  # 合計素材原価を計算するための変数
            material_entries = []

            for i in range(len(material_names)):
                material_name = material_names[i]
                quantity_used = quantities_used[i]

                if material_name and quantity_used:
                    material = Material.query.filter_by(name=material_name).first()
                    if material and int(quantity_used) <= material.quantity:
                        material.quantity -= int(quantity_used)
                        material_entry = RecipeMaterial(
                            recipe_id=new_recipe.id,
                            material_id=material.id,
                            quantity_used=int(quantity_used)
                        )
                        material_entries.append(material_entry)
                        
                        # 素材の合計原価を計算
                        total_material_cost += material.unit_price * int(quantity_used)
                    else:
                        db.session.rollback()
                        return render_template('new.html', error=f"{material_name}の在庫が不足しています。", form_data=request.form, materials=materials_data, categories=[c[0] for c in categories])
                else:
                    return render_template('new.html', error="素材名または使用量が不正です", form_data=request.form, materials=materials_data, categories=[c[0] for c in categories])

            # 合計原価と原価率の計算
            total_cost = total_material_cost + labor_cost
            profit_margin = (total_cost / listing_price * 100) if listing_price > 0 else 0

            # 合計原価と原価率をレシピに追加
            new_recipe.total_cost = total_cost
            new_recipe.profit_margin = profit_margin

            db.session.add_all(material_entries)
            db.session.commit()

            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            return render_template('new.html', error=f"エラーが発生しました: {str(e)}", form_data=request.form, materials=materials_data, categories=[c[0] for c in categories])
    else:
        return render_template('new.html', materials=materials_data, categories=[c[0] for c in categories])

@app.route('/recipes', methods=['GET'])
def recipe_list():
    recipes = Recipe.query.all()
    recipe_data = []

    for recipe in recipes:
        materials = RecipeMaterial.query.filter_by(recipe_id=recipe.id).all()
        
        # 素材の合計金額を計算
        total_material_cost = sum([material.quantity_used * material.material.unit_price for material in materials])
        
        # レシピ情報と素材合計金額を含む辞書を作成
        recipe_data.append({
            'recipe': recipe,
            'total_material_cost': total_material_cost
        })
    
    return render_template('recipe_list.html', recipe_data=recipe_data)




@app.route('/delete_recipe/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    # レシピに関連する素材の削除
    RecipeMaterial.query.filter_by(recipe_id=recipe_id).delete()
    
    db.session.delete(recipe)
    db.session.commit()
    return redirect(url_for('recipe_list'))

@app.route('/recipe_detail/<int:recipe_id>')
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    materials = RecipeMaterial.query.filter_by(recipe_id=recipe_id).all()
    
    # 素材の合計金額を計算
    total_material_cost = sum([material.quantity_used * material.material.unit_price for material in materials])
    
    return render_template('recipe_detail.html', recipe=recipe, materials=materials, total_material_cost=total_material_cost)

# レシピの編集
@app.route('/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    if request.method == 'POST':
        # フォームからデータを取得してレシピを更新
        recipe.name = request.form['name']
        recipe.description = request.form['description']
        recipe.labor_cost = float(request.form['labor_cost'])
        recipe.listing_price = float(request.form['listing_price'])

        # 現在のレシピに関連する素材の削除
        RecipeMaterial.query.filter_by(recipe_id=recipe.id).delete()
        db.session.flush()

        # 新しい素材情報の保存
        material_names = request.form.getlist('material_name')
        quantities_used = request.form.getlist('quantity_used')

        for i in range(len(material_names)):
            material_name = material_names[i]
            quantity_used = quantities_used[i]
            if material_name and quantity_used:
                material = Material.query.filter_by(name=material_name).first()
                if material and int(quantity_used) <= material.quantity:
                    material.quantity -= int(quantity_used)
                    material_entry = RecipeMaterial(
                        recipe_id=recipe.id,
                        material_id=material.id,
                        quantity_used=int(quantity_used)
                    )
                    db.session.add(material_entry)

        db.session.commit()
        return redirect(url_for('recipe_list'))

    # 編集用フォームに現在のデータを表示
    materials = Material.query.all()
    categories = db.session.query(Material.category).distinct().all()
    
    materials_data = [
        {
            "name": material.name,
            "category": material.category,
            "id": material.id,
            "quantity": material.quantity,
            "unit_price": material.unit_price,
            "supplier": material.supplier,
            "purchase_date": material.purchase_date.strftime('%Y-%m-%d') if material.purchase_date else None,
            "supplier_contact_or_notes": material.supplier_contact_or_notes
        } for material in materials
    ]

    form_data = {
        'name': recipe.name,
        'description': recipe.description,
        'labor_cost': recipe.labor_cost,
        'listing_price': recipe.listing_price,
        'material_name': [rm.material.name for rm in recipe.materials],
        'quantity_used': [rm.quantity_used for rm in recipe.materials]
    }

    return render_template('edit_recipe.html', recipe=recipe, materials=materials_data, categories=[c[0] for c in categories], form_data=form_data)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
