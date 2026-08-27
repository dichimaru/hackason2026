# Go の書き方入門 — このリポジトリで必要な範囲

| 項目 | 内容 |
|------|------|
| 対象読者 | Go / Gin が初めての人 |
| 範囲 | 掃除当番アプリのバックエンドを読み書きするのに必要な最小限 |
| このリポジトリの構成 | Go 1.22 + Gin v1.10 + GORM v1.31 (`gorm.io/driver/mysql`) |
| DB アクセス | GORM。SQL を直接書きたい場合は「6.8 生 SQL を書く」を参照 |
| 関連ドキュメント | [実装手順書](./implementation-guide.md) / [基本設計書](./basic-design.md) |

文法を網羅する文書ではない。**このリポジトリのコードを読んで真似できる状態**を目標にしている。
掲載しているコードは `gofmt` / `go vet` / `go build` を通したものと、既存コードからの引用である。

---

## 1. 読む前に: Go の3つの前提

**1. 型がある。ただし書く量は少ない。**

```go
var name string = "佐藤"   // 明示的に書ける
name2 := "佐藤"            // := なら型は推論される (関数の中だけで使える)
```

**2. エラーは戻り値で返す。例外 (try-catch) は無い。**

```go
value, err := doSomething()
if err != nil {
	return err        // これが Go で一番よく書くコード
}
```

**3. 名前の1文字目が大文字なら公開、小文字なら非公開。**

```go
type Duty struct {
	ID     int     // 他のパッケージから見える
	status string  // 同じパッケージ内からしか見えない (JSON にも出ない)
}
```

3番目は初心者がいちばん引っかかる。**JSON に出てこないフィールドは、まず大文字かどうかを疑う。**

---

## 2. Go の基本文法

### 2.1 ファイルの形

```go
package repository            // 1行目は必ず package。ディレクトリ名と揃える

import (
	"time"                    // 標準ライブラリ

	"gorm.io/gorm"            // 外部ライブラリ

	"github.com/hackason2026/webapp-go/internal/domain"   // 自分のコード
)
```

- **使っていない import はコンパイルエラーになる。** 逆に、使っている import が無いのもエラー。
- VS Code に Go 拡張を入れておくと、保存時に自動で追加・削除される。

### 2.2 関数

```go
func add(a int, b int) int {
	return a + b
}

// 戻り値を2つ返せる。Go では「値, エラー」の形が定番
func divide(a int, b int) (int, error) {
	if b == 0 {
		return 0, errors.New("divide by zero")
	}
	return a / b, nil
}
```

### 2.3 変数と代入

```go
count := 0            // 新しく宣言 + 代入
count = 1             // すでにある変数への代入 (: が付かない)

var duties []Duty     // 宣言だけ。ゼロ値 (slice なら nil) になる
```

| 書き方 | 意味 | 間違いやすい点 |
|--------|------|---------------|
| `:=` | 宣言と代入を同時に | 同じ変数に2回使うとエラー |
| `=` | 代入のみ | 宣言していない変数に使うとエラー |

**宣言したのに使わない変数はコンパイルエラー**になる (`declared and not used`)。デバッグ中に消し忘れないこと。

### 2.4 if / for

```go
if err != nil {
	return err
}

// if の中で変数を作れる。この err は if の中だけで有効
if err := doSomething(); err != nil {
	return err
}

for i := 0; i < 5; i++ {         // 普通のループ
}

for _, duty := range duties {    // slice を回す。_ は「使わない」の意味
	fmt.Println(duty.ID)
}

for i < 10 {                     // 条件だけの while 相当
	i++
}
```

Go には `while` が無く、`for` だけで書く。

### 2.5 slice (可変長配列) と map

```go
ids := []int{1, 2, 3}          // slice リテラル
ids = append(ids, 4)           // 追加は append。戻り値を代入し直すのを忘れない
fmt.Println(len(ids))          // 長さ

out := []domain.Duty{}         // 空の slice (JSON では [] になる)
var out2 []domain.Duty         // nil の slice (JSON では null になる)

allowed := map[string]bool{"pending": true, "done": true}
if allowed["done"] {           // キーが無ければゼロ値 (false) が返る
}
value, ok := allowed["xxx"]    // 存在確認したいときは2つ受け取る
```

**API で「0件のときに `null` ではなく `[]` を返したい」なら `out := []T{}` で初期化する。**
このリポジトリの `repository` が全部そうしているのはこのため。

### 2.6 struct とメソッド

```go
// 構造体 = データのまとまり (他言語のクラスのフィールド部分に相当)
type Duty struct {
	ID            int    `json:"id"`
	EmployeeID    int    `json:"employee_id"`
	ScheduledDate string `json:"scheduled_date"`
}

// メソッド = 型に紐づく関数。(r DutyRepo) の部分をレシーバと呼ぶ
type DutyRepo struct{ DB *gorm.DB }

func (r DutyRepo) List() ([]Duty, error) {
	// r.DB でフィールドにアクセスできる
	return nil, nil
}
```

呼び出し側:

```go
repo := DutyRepo{DB: conn}
duties, err := repo.List()
```

### 2.7 ポインタ (最小限)

`*` と `&` が出てくるが、このリポジトリで覚えることは2つだけ。

```go
var duties []Duty
err := db.Find(&duties).Error  // & = 「この変数の場所」を渡す。書き込んでもらうときに使う

func (h *Handler) Health(c *gin.Context) {}   // * = ポインタ型。中身を書き換えられる
```

`Find` や `ShouldBindJSON` のように**「変数に値を入れてもらう」関数には `&` を付ける**、と覚えておけばよい。

---

## 3. error と defer

### 3.1 error

```go
func (r EmployeeRepo) List() ([]domain.Employee, error) {
	out := []domain.Employee{}
	if err := r.DB.Order("id").Find(&out).Error; err != nil {
		return nil, err        // 自分で処理できないなら、そのまま上に返す
	}
	return out, nil            // 成功時の error は nil
}
```

- **`err` を無視しない。** 受け取ったら必ず `if err != nil` を書く。
- 自分でエラーを作るときは `errors.New("...")` か `fmt.Errorf("...: %w", err)`。
- HTTP のステータスに変換するのは `handler` の仕事。`repository` は素直に返すだけでよい。

### 3.2 defer

`defer` を付けた処理は、**関数を抜けるときに必ず実行される**。後片付けに使う。

```go
f, err := os.Open("data.csv")
if err != nil {
	return err
}
defer f.Close()         // どこで return してもここが実行される
```

GORM を使う場合、接続の後片付けは GORM 側がやるので `defer` を書く場面は少ない。
ファイルを開いたときや、自分で `sql.Tx` を扱うときに使う。

---

## 4. JSON との対応 (構造体タグ)

`internal/domain/model.go` の実物:

```go
type Employee struct {
	ID         int    `json:"id"`
	Name       string `json:"name"`
	Email      string `json:"email"`
	Department string `json:"department"`
	Active     bool   `json:"active"`
}
```

これが JSON になると:

```json
{ "id": 1, "name": "佐藤 一郎", "email": "sato.ichiro@example.com", "department": "営業部", "active": true }
```

| 書き方 | 結果 |
|--------|------|
| `Name string \`json:"name"\`` | `"name": "..."` |
| `Name string` (タグ無し) | `"Name": "..."` (フィールド名がそのまま出る) |
| `name string` (小文字) | **JSON に出ない** |
| `Memo string \`json:"memo,omitempty"\`` | 空のときキーごと省略 |
| `Secret string \`json:"-"\`` | 常に出さない |

**API のレスポンスに項目を増やすときは `domain` の構造体にフィールドを足す。**
DB の列を増やす場合は `webapp/sql/0_schema.sql` も直して `make seed` する
(モデルにフィールドを足しただけでは列は増えない)。

---

## 5. Gin の書き方

### 5.1 ハンドラの形

```go
func (h *Handler) ListAreas(c *gin.Context) {
	out, err := h.Areas.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return                       // ← return を忘れると処理が続いてしまう
	}
	c.JSON(http.StatusOK, out)
}
```

`gin.H` は `map[string]interface{}` の別名で、その場限りの JSON を作るのに使う。

### 5.2 入力の受け取り方

| 取りたいもの | 書き方 | 例 |
|-------------|--------|-----|
| パスの一部 | `c.Param("id")` | `/api/duties/:id` → `"12"` (文字列) |
| クエリ文字列 | `c.Query("status")` | `/api/duties?status=done` |
| クエリ (既定値付き) | `c.DefaultQuery("status", "pending")` | |
| JSON ボディ | `c.ShouldBindJSON(&req)` | `{"status":"done"}` |

```go
id, err := strconv.Atoi(c.Param("id"))     // パスパラメータは文字列なので変換する
if err != nil {
	c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
	return
}

type updateDutyStatusRequest struct {
	Status string `json:"status" binding:"required"`
}

var req updateDutyStatusRequest
if err := c.ShouldBindJSON(&req); err != nil {
	c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
	return
}
```

`binding:"required"` を付けると、値が空のときに `ShouldBindJSON` がエラーを返す。

### 5.3 ステータスコードの使い分け

| 定数 | 値 | 使う場面 |
|------|-----|---------|
| `http.StatusOK` | 200 | 成功 |
| `http.StatusCreated` | 201 | 作成に成功 (今回は 200 で統一している) |
| `http.StatusBadRequest` | 400 | リクエストの内容がおかしい |
| `http.StatusNotFound` | 404 | 対象が存在しない |
| `http.StatusInternalServerError` | 500 | サーバ側の失敗 (DB エラーなど) |

### 5.4 ルーティング

```go
api := r.Group("/api")
{
	api.GET("/duties", h.ListDuties)
	api.POST("/duties/generate", h.GenerateDuties)
	api.PATCH("/duties/:id", h.UpdateDutyStatus)
}
```

`r.Group("/api")` でまとめているので、各行のパスに `/api` は書かない。

---

## 6. データベースアクセス (GORM)

このリポジトリは ORM に [GORM](https://gorm.io/ja_JP/docs/) を使う。SQL を文字列で書く代わりに、
構造体とメソッドチェーンで問い合わせを組み立てる。

### 6.1 モデル = テーブルの1行

`internal/domain/model.go` の実物:

```go
type Employee struct {
	ID         uint      `gorm:"primaryKey" json:"id"`
	Name       string    `json:"name"`
	Email      string    `json:"email"`
	Department string    `json:"department"`
	Active     bool      `json:"active"`
	CreatedAt  time.Time `json:"-"`
}

func (Employee) TableName() string { return "employees" }
```

| 決まりごと | 説明 |
|-----------|------|
| フィールド名 → 列名 | `EmployeeID` は自動で `employee_id` に対応する (スネークケース変換) |
| `gorm:"primaryKey"` | 主キーの指定 |
| `TableName()` | テーブル名を明示する。書かないと GORM が複数形を推測する |
| `CreatedAt` | この名前のフィールドは GORM が作成時刻を自動で入れる |
| `json:"-"` | API のレスポンスに出したくないフィールドに付ける |

**テーブル定義は `webapp/sql/0_schema.sql` が正。** GORM の `AutoMigrate` はこのリポジトリでは呼ばない
(呼ぶと GORM がテーブルを作り替え、SQL ファイルと二重管理になる)。カラムを増やすときは
`0_schema.sql` を直して `make seed` し、モデルにフィールドを足す、の順で行う。

### 6.2 関連 (JOIN 相当)

```go
type Duty struct {
	ID            uint      `gorm:"primaryKey"`
	EmployeeID    uint      `gorm:"not null"`
	AreaID        uint      `gorm:"not null"`
	ScheduledDate time.Time `gorm:"type:date;not null"`
	Status        string    `gorm:"not null;default:pending"`
	CreatedAt     time.Time

	Employee Employee `gorm:"foreignKey:EmployeeID"`
	Area     Area     `gorm:"foreignKey:AreaID"`
}
```

`Employee` / `Area` は**そのテーブルの列ではなく、関連の置き場所**。`Preload` を書いたときだけ中身が埋まる。

### 6.3 取得

```go
// 全件 (SELECT * FROM employees ORDER BY id)
out := []domain.Employee{}
if err := r.DB.Order("id").Find(&out).Error; err != nil {
	return nil, err
}

// 1件 (見つからなければ gorm.ErrRecordNotFound)
var duty domain.Duty
if err := r.DB.First(&duty, id).Error; err != nil {
	return nil, err
}

// 条件付き
var duties []domain.Duty
err := r.DB.Where("status = ?", "pending").Find(&duties).Error

// 1列だけ取り出す (SELECT id FROM employees WHERE active = true)
ids := []uint{}
err = r.DB.Model(&domain.Employee{}).Where("active = ?", true).Pluck("id", &ids).Error
```

守ること:

1. **結果を入れる変数には `&` を付ける** (`Find(&out)`)。GORM がそこに書き込む。
2. **エラーは `.Error` で取り出す。** メソッドチェーンの戻り値は `*gorm.DB` なので、`err :=` では受け取れない。
3. 条件の値は `Where("status = ?", value)` のように `?` で渡す。文字列連結にするとインジェクションになる。
4. `out := []domain.Employee{}` と初期化しておくと、0件のとき JSON が `null` ではなく `[]` になる。

### 6.4 関連を一緒に取る (Preload)

`internal/repository/duty.go` の実物:

```go
func (r DutyRepo) List() ([]domain.DutyView, error) {
	duties := []domain.Duty{}
	err := r.DB.
		Preload("Employee").
		Preload("Area").
		Order("scheduled_date").
		Order("area_id").
		Find(&duties).Error
	if err != nil {
		return nil, err
	}

	out := make([]domain.DutyView, 0, len(duties))
	for _, d := range duties {
		out = append(out, domain.DutyView{
			ID:            d.ID,
			EmployeeID:    d.EmployeeID,
			EmployeeName:  d.Employee.Name,
			AreaID:        d.AreaID,
			AreaName:      d.Area.Name,
			ScheduledDate: d.ScheduledDate.Format("2006-01-02"),
			Status:        d.Status,
		})
	}
	return out, nil
}
```

- `Preload("Employee")` の引数は**フィールド名**(`Employee`)。テーブル名 (`employees`) ではない。
- API の応答は社員名・エリア名を平坦に持つ `DutyView` なので、モデルから詰め替えている。
  モデル (DB の形) と API の形を分けておくと、片方を変えてももう片方が壊れない。
- `Preload` は関連ごとに別のクエリを投げる。件数が増えて遅くなったら `Joins` か生 SQL に変える。

### 6.5 追加

```go
duty := domain.Duty{EmployeeID: 1, AreaID: 2, ScheduledDate: date, Status: "pending"}
if err := r.DB.Create(&duty).Error; err != nil {
	return err
}
// Create のあと duty.ID に採番された値が入っている

// スライスを渡すとまとめて INSERT される
err := r.DB.Create(&duties).Error
```

**関連フィールドを持つモデルを Create するときは注意。** ゼロ値の `Employee` / `Area` を
GORM が新規レコードとして書き込もうとするため、`Omit` で外す。`duty.go` の実物:

```go
err := r.DB.Transaction(func(tx *gorm.DB) error {
	return tx.Omit("Employee", "Area").Create(&items).Error
})
```

### 6.6 更新

```go
res := r.DB.Model(&domain.Duty{}).Where("id = ?", id).Update("status", status)
if res.Error != nil {
	return false, res.Error
}
updated := res.RowsAffected > 0     // 0 なら該当行が無かった

// 複数列をまとめて更新するときは Updates + map
r.DB.Model(&domain.Duty{}).Where("id = ?", id).
	Updates(map[string]interface{}{"status": "done", "area_id": 3})
```

`Updates` に構造体を渡すとゼロ値の列が無視される (0 や空文字に更新できない)。
**明示的に更新したい列があるときは map を使う。**

### 6.7 トランザクション

```go
err := r.DB.Transaction(func(tx *gorm.DB) error {
	if err := tx.Create(&a).Error; err != nil {
		return err          // error を返すと自動で Rollback
	}
	return tx.Create(&b).Error
})                              // nil を返すと自動で Commit
```

関数の中では `r.DB` ではなく**引数の `tx`** を使う。`r.DB` を使うとトランザクションの外になる。

### 6.8 生 SQL を書く

集計など、ORM で書くと読みにくい処理は SQL を直接書ける。

```go
type dutyCount struct {
	EmployeeID uint
	Total      int
}
var rows []dutyCount
err := r.DB.Raw(
	"SELECT employee_id, COUNT(*) AS total FROM duties GROUP BY employee_id",
).Scan(&rows).Error

// 結果を返さない SQL は Exec
err = r.DB.Exec("UPDATE duties SET status = ? WHERE scheduled_date < ?", "done", date).Error
```

`Raw` / `Exec` でも値は `?` で渡す。列名 (`employee_id`) は構造体のフィールド名 (`EmployeeID`) に自動で対応する。

### 6.9 発行された SQL を見る

期待と違う結果になったら、まず SQL を見る。`internal/db/db.go` のログレベルを上げる。

```go
cfg := &gorm.Config{
	Logger: logger.Default.LogMode(logger.Info),   // Warn → Info
}
```

`make up` して `docker logs -f cleaning-webapp` を見ると、実行された SQL が1行ずつ出る。

## 7. 組み立て方 (依存の渡し方)

Go には DI フレームワークを使わず、`main` で組み立てて渡す書き方が一般的。

```go
// cmd/server/main.go
func main() {
	cfg := config.Load()          // 環境変数を読む
	conn := db.MustOpen(cfg)      // DB に接続 (起動待ちリトライ付き)
	h := handler.New(conn)        // ハンドラに DB を渡す
	r := router.New(h)            // ルータにハンドラを渡す

	if err := r.Run(":" + cfg.Port); err != nil {
		log.Fatal(err)
	}
}
```

```go
// internal/handler/handler.go
func New(db *gorm.DB) *Handler {
	er := repository.EmployeeRepo{DB: db}
	ar := repository.AreaRepo{DB: db}
	dr := repository.DutyRepo{DB: db}
	return &Handler{
		DB:        db,
		Employees: er,
		Areas:     ar,
		Duties:    dr,
		Generator: service.DutyGenerator{Employees: er, Areas: ar, Duties: dr},
	}
}
```

**リポジトリを1つ増やしたら、この `New` にも足す。** ここに足さないとハンドラから呼べない。

---

## 8. よくある詰まりどころ

| メッセージ / 症状 | 意味 | 対処 |
|------------------|------|------|
| `declared and not used: x` | 変数を宣言して使っていない | 使うか消す。Go は警告ではなくエラーにする |
| `"strconv" imported and not used` | import が余っている | 消す |
| `undefined: strconv` | import が足りない | import に足す |
| `cannot use x (type int) as type string` | 型が違う | `strconv.Atoi` / `strconv.Itoa` で変換する |
| `non-declaration statement outside function body` | 関数の外にコードを書いた | 波かっこの対応を確認する |
| `no new variables on left side of :=` | 既にある変数に `:=` を使った | `=` にする |
| `missing return` | 戻り値のある関数で return していない経路がある | すべての分岐で return する |
| JSON にフィールドが出ない | フィールドが小文字 | 大文字で始める + `json:"..."` タグを付ける |
| 0件のとき `null` が返る | slice が nil のまま | `out := []T{}` で初期化する |
| `err :=` で受け取れない | GORM のメソッドチェーンは `*gorm.DB` を返す | 末尾に `.Error` を付ける |
| `record not found` | `First` で該当行が無かった | `errors.Is(err, gorm.ErrRecordNotFound)` で判定し 404 を返す |
| 更新したのに値が変わらない | `Updates` に構造体を渡し、ゼロ値が無視された | `Update("列名", 値)` か map を使う |
| 関連テーブルに空行が増えた | Create 時にゼロ値の関連が一緒に書き込まれた | `Omit("Employee", "Area")` を付ける |
| 関連が空 (`""` や 0) になる | `Preload` を書いていない | `Preload("Employee")` を追加する (引数はフィールド名) |
| `Error 1054: Unknown column` | 列名の綴り違い、モデルと DB のずれ | Adminer で列を確認。SQL を見たいときは Logger を `Info` に |
| `Error 1452: Cannot add or update a child row` | 外部キー制約違反 (存在しない employee_id など) | 参照先が存在するか確認する |
| `panic: runtime error: invalid memory address` | nil のものを触った | ポインタが nil でないか、`New` で渡し忘れていないか確認 |

---

## 9. 整形・静的解析・ビルド

Go には標準で整形ツールが付いている。**整形は好みではなく統一ルール**なので、必ず通す。

```bash
gofmt -l .        # 整形されていないファイル名を表示 (何も出なければ OK)
gofmt -w .        # 整形して上書き
go vet ./...      # 怪しい書き方の検出
go build ./...    # コンパイル確認
```

Go をローカルに入れていない場合は Docker で同じことができる。

```bash
docker run --rm -v "$PWD/webapp/go":/src -w /src golang:1.22-alpine \
  sh -c "gofmt -l . && go vet ./... && go build ./..."
```

VS Code なら Go 拡張 (`golang.go`) を入れると、保存時に整形と import 整理が走る。

---

## 付録A. Preload と Joins の使い分け

`Preload` は関連ごとに別クエリを投げる。1クエリにまとめたい場合は `Joins` を使う。

```go
// Preload: SELECT * FROM duties → SELECT * FROM employees WHERE id IN (...) → areas も同様 (計3クエリ)
r.DB.Preload("Employee").Preload("Area").Find(&duties)

// Joins: 1クエリで JOIN する
r.DB.Joins("Employee").Joins("Area").Find(&duties)
```

| | Preload | Joins |
|---|---------|-------|
| クエリ数 | 関連の数だけ増える | 1回 |
| 件数が多いとき | 遅くなりやすい | 有利 |
| 1対多の関連 | 使える | 重複行が出るため不向き |
| 読みやすさ | 分かりやすい | 条件が絡むとやや複雑 |

このリポジトリは25件程度なので `Preload` で十分。件数が増えて遅くなったら `Joins` か
「6.8 生 SQL を書く」に切り替える。

判断に迷ったら **まず Preload で動かし、遅くなってから変える**。
