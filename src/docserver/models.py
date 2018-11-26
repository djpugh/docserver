from docserver import db


class Language(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    packages = db.relationship('Package', backref='language', lazy=True)

    def __repr__(self):
        return f'<Language {self.name}>'


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    packages = db.relationship('Package', backref='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.name}>'


class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'), nullable=False)
    repository = db.Column(db.String(300), unique=True, nullable=False)

    def __repr__(self):
        return f'<Package {self.name} ({self.customer})>'


if __name__ == "__main__":
    db.create_all()
