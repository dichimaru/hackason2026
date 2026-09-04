# 実装手順書 — 社内掃除当番アプリ (Go + Next.js)

| 項目 | 内容 |
|------|------|
| 対象読者 | ハッカソン参加者。Go / Gin が初めての人を想定 |
| 前提 | Docker Desktop が動くこと。Go 本体のローカルインストールは不要 |
| 採用スタック | バックエンド: Go (Gin + GORM) / フロントエンド: Next.js / DB: MySQL 8.0 |
| 関連ドキュメント | [Go の書き方入門](./go-guide.md) / [API 仕様書](./api-spec.md) / [基本設計書](./basic-design.md) / [テーブル定義書](./table-definition.md) |

この文書は「環境を立ち上げてから、機能を1つ追加してコミットするまで」の手順書である。
Go の文法や Gin の書き方そのものは [Go の書き方入門](./go-guide.md) に分けてある。

---

## 1. 準備

### 1.1 必要なもの

| ツール | 必須 | 用途 | 備考 |
|--------|:----:|------|------|
| Docker Desktop (Compose v2) | ○ | コンテナ起動 | これだけで Go も Node も動く |
| GNU Make | ○ | 起動ショートカット | 無い場合は README の「make が無い環境でも動かす」を参照 |
| Git | ○ | リポジトリ取得 | |
| エディタ (VS Code など) | ○ | コード編集 | |
| Go 本体 | — | 補完・`gofmt`・`go vet` をローカルで動かしたい人向け | `brew install go` (Mac) |

**Go をローカルに入れなくても実装できる。** ビルドは Docker の `golang:1.22-alpine` イメージの中で行われるため、
`make up` するだけでコンパイルされる。エディタの補完を効かせたい場合だけ入れればよい。

ポート `8080` / `8081` / `3306` を使うので空けておく。

### 1.2 起動して動くことを確認する

```bash
git clone <このリポジトリのURL> hackason2026
cd hackason2026
make up          # 既定が Go + Next.js なので引数は不要
make ps          # 5サービス (db / webapp / frontend / nginx / adminer) が Up
```

初回はイメージのビルドに数分かかる。以下がすべて通れば準備完了。

| 確認すること | コマンド / URL | 期待する結果 |
|--------------|----------------|--------------|
| API が生きている | `curl http://localhost:8080/api/health` | `{"status":"ok"}` |
| 社員データが入っている | `curl http://localhost:8080/api/people` | 30件の JSON 配列 |
| 抽選結果データが入っている | `curl http://localhost:8080/api/lottery-results` | 25件の JSON 配列 |
| 画面が出る | <http://localhost:8080> | 社員一覧と当番一覧が表示される |
| DB を見られる | <http://localhost:8081> | Adminer のログイン画面 |

Windows の PowerShell では `curl` の代わりに `Invoke-RestMethod` を使う。

### 1.3 DB の中を見る (Adminer)

<http://localhost:8081> に以下で入る。

| 項目 | 値 |
|------|-----|
| System | `MySQL` |
| Server | `db` |
| Username | `cleaning` |
| Password | `cleaning` |
| Database | `cleaning` |

SQL を直接実行できるので、API の結果が変だと思ったらまず DB の中身を見る。

---

## 2. 全体像

### 2.1 リクエストがどこを通るか

```
ブラウザ
  │  http://localhost:8080/api/lottery-results
  ▼
nginx ────────────▶ webapp (Go)                        ────────▶ db (MySQL)
  │  /api/* だけ      router → handler → service → repository
  │
  └── / (その他) ──▶ frontend (Next.js)
```

`/api/` で始まるパスだけが Go 側に届く。それ以外は Next.js が返す。
同じ `localhost:8080` から配信されるので、フロントは `/api/...` と相対パスで書けばよく、CORS の設定は不要。

### 2.2 やりたいこと → 触る場所

| やりたいこと | 触るファイル |
|--------------|-------------|
| API を1本増やす | `webapp/go/internal/handler/handler.go` + `internal/router/router.go` |
| DB アクセス (GORM のクエリ) を書く・変える | `webapp/go/internal/repository/*.go` |
| 当番の割当ロジックを変える | `webapp/go/internal/service/duty_generator.go` |
| API が返す JSON の項目を増やす | `webapp/go/internal/domain/model.go` (モデル / `DutyView`) |
| テーブルを追加・変更する | `webapp/sql/0_schema.sql` (+ `1_seed.sql`) |
| 画面の見た目・操作を変える | `webapp/frontend/next/pages/index.tsx` |
| 画面を1枚増やす | `webapp/frontend/next/pages/` に `xxx.tsx` を追加 (ファイル名 = URL) |
| DB 接続の設定を変える | `webapp/go/internal/config/config.go`, `internal/db/db.go` |
| 環境変数を追加する | `internal/config/config.go` + `development/compose-backend-go.yml` |

### 2.3 レイヤと責務

Go 側は4層に分かれている。**上の層は下の層を呼ぶが、下の層は上を知らない。**

| レイヤ | ディレクトリ | やること | やらないこと |
|--------|-------------|---------|-------------|
| ルーティング | `internal/router/` | パスとハンドラの対応付け | 処理そのもの |
| ハンドラ | `internal/handler/` | 入力の受け取り、JSON 応答、HTTP ステータスの決定 | SQL を書く |
| サービス | `internal/service/` | 業務ロジック (当番の割当など) | `*gin.Context` を触る |
| リポジトリ | `internal/repository/` | GORM でのDBアクセスと結果の詰め替え | HTTP のことを考える |

守るとよい約束は3つ。

1. **DB アクセスは `repository` にだけ書く。** ハンドラに GORM のクエリを書くと、あとで再利用もテストもできなくなる。
2. **`*gin.Context` は `handler` から外に出さない。** `service` が Gin を知らなければ、ロジックだけを別の場所から呼べる。
3. **迷ったらまず動かす。** 層をまたぐ判断で止まるより、動く形にしてから寄せた方が速い (ハッカソンなので)。

---

## 3. 変更を反映する手順

**このリポジトリはホットリロードしない。** Go もフロントも本番ビルドで動いているため、
コードを直したらコンテナを作り直す必要がある。

| 直したもの | 反映のコマンド | 所要 | 注意 |
|-----------|---------------|------|------|
| Go のコード | `make up` | 20秒〜1分 | 差分ビルドなので2回目以降は速い |
| フロントのコード | `make up` | 30秒〜2分 | `next build` が走る |
| `webapp/sql/*.sql` | `make seed` | 30秒〜1分 | **DB の中身が消えて初期状態に戻る** |
| compose / nginx の設定 | `make restart` | 30秒〜1分 | |

`make up` は変更が無いサービスは作り直さないので、そのまま何度でも叩いてよい。

反映されたか分からないときは、この順で見る。

```bash
make ps                         # webapp が Up か。Exit していたら起動失敗
make logs                       # 全サービスのログ (Ctrl+C で抜ける)
docker logs cleaning-webapp     # Go だけのログを見る
```

**ビルドに失敗すると `make up` の出力にコンパイルエラーが出て、コンテナは古いまま動き続ける。**
「直したのに反映されない」ときは、まず `make up` の出力を上にスクロールしてエラーを探す。

---

## 4. 機能を1つ追加する手順 (型)

どの機能でもこの順で進めると迷いにくい。

```
1. 決める      どの API / 画面を作るか、リクエストとレスポンスの形を決める
2. DB          テーブルやカラムが足りなければ 0_schema.sql を直して make seed
3. repository  必要な問い合わせをメソッドとして追加する (GORM)
4. service     業務ロジックが必要なら追加する (単純な取得・更新なら飛ばしてよい)
5. handler     入力を検証して repository/service を呼び、JSON を返す
6. router      パスとハンドラを結びつける
7. 確認        make up して curl で叩く
8. frontend    画面から呼ぶ
9. 確認        ブラウザで操作して確認する
```

DB を触らない機能なら 2 は飛ばす。画面が不要な API だけの追加なら 8・9 も飛ばす。

---

## 5. ワークスルー: 当番を「実施済み」にする API を追加する

現状、抽選結果の状態 (`lottery_result.status`) を `pending` から変える手段が無い
(基本設計書の「制約事項 #3」)。これを解消する `PATCH /api/lottery-results/:id` を追加する。

以下のコードは `gofmt` / `go vet` / `go build` を通したものを載せている。

### 5.1 決めること

| 項目 | 内容 |
|------|------|
| メソッド / パス | `PATCH /api/lottery-results/:id` |
| リクエストボディ | `{"status": "done"}` |
| 成功レスポンス | `200 {"id": 1, "status": "done"}` |
| 失敗レスポンス | `400` (id や status が不正) / `404` (当番が無い) / `500` (DB エラー) |

`status` は DB 側が `ENUM('pending','done','swapped')` なので、この3つ以外は受け付けない。

### 5.2 手順1: リポジトリに更新メソッドを追加する

`webapp/go/internal/repository/duty.go` の末尾に追加する。

```go
// UpdateStatus は当番の状態を更新する。該当する当番が無ければ false を返す。
func (r DutyRepo) UpdateStatus(id uint, status string) (bool, error) {
	res := r.DB.Model(&domain.Duty{}).Where("id = ?", id).Update("status", status)
	if res.Error != nil {
		return false, res.Error
	}
	return res.RowsAffected > 0, nil
}
```

ポイント:

- `Model(&domain.Duty{})` で対象テーブルを指定する。これが無いと GORM はどのテーブルか判断できない。
- 条件の値は `Where("id = ?", id)` のように `?` で渡す。文字列連結にするとインジェクションになる。
- エラーは戻り値の `.Error`、更新件数は `.RowsAffected` で取る。存在しない id でもエラーにはならず 0件更新になる。
- 1列だけなら `Update("列名", 値)`。複数列なら `Updates(map[string]interface{}{...})` を使う
  (`Updates` に構造体を渡すとゼロ値の列が無視される)。

### 5.3 手順2: ハンドラを追加する

`webapp/go/internal/handler/handler.go` の import に `strconv` を足し、末尾に追加する。

```go
import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"github.com/hackason2026/webapp-go/internal/repository"
	"github.com/hackason2026/webapp-go/internal/service"
)
```

```go
type updateDutyStatusRequest struct {
	Status string `json:"status" binding:"required"`
}

// duties.status は ENUM なので、受け取る値を先に絞る。
var allowedDutyStatus = map[string]bool{"pending": true, "done": true, "swapped": true}

func (h *Handler) UpdateDutyStatus(c *gin.Context) {
	id64, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil || id64 == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}
	id := uint(id64)

	var req updateDutyStatusRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if !allowedDutyStatus[req.Status] {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid status"})
		return
	}

	updated, err := h.Duties.UpdateStatus(id, req.Status)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if !updated {
		c.JSON(http.StatusNotFound, gin.H{"error": "duty not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"id": id, "status": req.Status})
}
```

ポイント:

- URL の `:id` は文字列で届くので数値にする。モデルの ID は `uint` なので `strconv.ParseUint` を使う。変換失敗は 400。
- `c.ShouldBindJSON` でボディを構造体に流し込む。`binding:"required"` があると空のときエラーになる。
- 「DB に無い」は 500 ではなく 404。エラーの種類ごとに返すステータスを分けると、フロント側で扱いやすい。
- `return` を忘れると、エラー応答を返した後に処理が続いてしまう。Go は `c.JSON` を呼んでも自動で止まらない。

### 5.4 手順3: ルーティングに登録する

`webapp/go/internal/router/router.go`。

```go
	api := r.Group("/api")
	{
		api.GET("/health", h.Health)
		api.GET("/employees", h.ListEmployees)
		api.GET("/areas", h.ListAreas)
		api.GET("/duties", h.ListDuties)
		api.POST("/duties/generate", h.GenerateDuties)
		api.PATCH("/duties/:id", h.UpdateDutyStatus)
	}
```

**ここを忘れると 404 になる。** ハンドラを書いただけでは繋がらない。

### 5.5 手順4: 起動して確認する

```bash
make up

# 1件目の当番を done にする
curl -X PATCH http://localhost:8080/api/lottery-results/1 \
  -H 'Content-Type: application/json' \
  -d '{"status":"done"}'
# → {"id":1,"status":"done"}

# 一覧に反映されているか
curl -s http://localhost:8080/api/lottery-results | head -c 300

# 異常系も見ておく
curl -i -X PATCH http://localhost:8080/api/lottery-results/99999 \
  -H 'Content-Type: application/json' -d '{"status":"done"}'   # → 404
curl -i -X PATCH http://localhost:8080/api/lottery-results/1 \
  -H 'Content-Type: application/json' -d '{"status":"xxx"}'     # → 400
```

### 5.6 手順5: 画面から呼べるようにする

`webapp/frontend/next/pages/index.tsx` に関数を追加する。

```tsx
  const markDone = async (id: number) => {
    await fetch(`/api/lottery-results/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "done" }),
    });
    await load();
  };
```

当番一覧のテーブルに列を1つ増やす。

```tsx
        <thead>
          <tr>
            <th style={th}>日付</th>
            <th style={th}>エリア</th>
            <th style={th}>担当</th>
            <th style={th}>状態</th>
            <th style={th}>操作</th>
          </tr>
        </thead>
        <tbody>
          {duties.map((d) => (
            <tr key={d.id}>
              <td style={td}>{d.scheduled_date}</td>
              <td style={td}>{d.area_name}</td>
              <td style={td}>{d.employee_name}</td>
              <td style={td}>{d.status}</td>
              <td style={td}>
                {d.status === "pending" && (
                  <button onClick={() => markDone(d.id)}>完了</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
```

### 5.7 手順6: ブラウザで確認する

```bash
make up
```

<http://localhost:8080> を開き、「完了」ボタンを押して状態が `done` に変わることを確認する。

### 5.8 仕上げ

- **[API 仕様書](./api-spec.md) を直す。** この例なら「7.1 PATCH /api/lottery-results/{id}」を確定仕様として
  「5. エンドポイント詳細」へ移し、エンドポイント一覧の状態を「確定」にする。
- 設計書に手を入れる。この例なら基本設計書の「機能一覧」「制約事項 #3」が対象。
- md を直したら `make docs` で xlsx を作り直す。
- コミットする (「8. 複数人で進めるとき」を参照)。

---

## 6. 動作確認のやり方

### 6.1 curl で API を叩く

```bash
curl http://localhost:8080/api/health
curl http://localhost:8080/api/people
curl http://localhost:8080/api/tasks
curl http://localhost:8080/api/lottery-results
curl -X POST http://localhost:8080/api/lottery-results/generate
```

見やすくしたいときは `| python3 -m json.tool` を後ろに付ける。
ステータスコードやヘッダも見たいときは `-i` を付ける。

### 6.2 Adminer で DB を見る

想定どおり書けているかは SQL で直接確認する。

```sql
SELECT status, COUNT(*) FROM duties GROUP BY status;
SELECT * FROM duties ORDER BY id DESC LIMIT 10;
```

### 6.3 ログを見る

```bash
docker logs -f cleaning-webapp    # Go のログ (Gin が全リクエストを1行ずつ出す)
docker logs -f cleaning-frontend  # Next.js
make logs                         # 全部まとめて
```

Gin のログには `[GIN] ... | 200 | ... | PATCH /api/lottery-results/1` のようにステータスとパスが出る。
**404 なら router に登録できていない、500 ならハンドラの中でエラーになっている**、という切り分けができる。

---

## 7. エラーの読み方とよくある詰まり

| 症状 | よくある原因 | 対処 |
|------|-------------|------|
| `make up` の途中でコンパイルエラー | Go の文法・型の間違い | エラー行を直す。[Go の書き方入門](./go-guide.md)「よくある詰まりどころ」も参照 |
| `declared and not used` | 変数を宣言して使っていない | Go はこれをエラーにする。使わないなら消す |
| `undefined: xxx` | 関数名・パッケージ名の間違い、import 忘れ | import を確認。VS Code なら保存時に自動追加できる |
| API が 404 | `router.go` への登録忘れ、パスの綴り違い | ルーティングを確認 |
| API が 500 | ハンドラ内のエラー (DB アクセスの失敗が多い) | `docker logs cleaning-webapp` でエラー本文を見る |
| 関連が空 (社員名が `""`) | `Preload` の書き忘れ | `Preload("Employee")` を追加する |
| 発行されている SQL が知りたい | — | `internal/db/db.go` の Logger を `logger.Info` にして `make up` |
| API が 400 | リクエストボディの形が違う、`Content-Type` 未指定 | curl に `-H 'Content-Type: application/json'` を付ける |
| JSON に項目が出てこない | 構造体のフィールドが小文字 (非公開) / タグ無し | フィールド名を大文字で始め、`json:"..."` を付ける |
| 画面を直したのに変わらない | `make up` していない | フロントも本番ビルドなので再ビルドが必要 |
| `port is already allocated` | 8080 などを他プロセスが使用中 | `make down`、または該当プロセスを止める |
| DB 接続エラーで webapp が落ちる | DB の起動待ちで失敗 | 通常は最大60秒リトライする。それでも駄目なら `make restart` |
| データが古い / 壊れた | シードを変えた、いじりすぎた | `make seed` で初期化 (中身は消える) |
| 日本語が文字化けする | 接続文字セットの不一致 | 既に `utf8mb4` で揃えてある。追加の SQL でも `SET NAMES utf8mb4;` を前提にする |

---

## 8. 複数人で進めるとき

### 8.1 コンフリクトしやすい場所

| ファイル | 理由 | 対策 |
|----------|------|------|
| `internal/handler/handler.go` | 全員がハンドラを足す | 追加は**ファイル末尾**に。あるいは機能ごとに `handler_duty.go` などへ分ける |
| `internal/router/router.go` | 全員が1行足す | 1行なので解消は簡単。上書きせずに両方残す |
| `pages/index.tsx` | 画面が1枚しかない | 担当を分けるか、コンポーネントを別ファイルに切り出す |
| `webapp/sql/0_schema.sql` | テーブル追加が重なる | 誰が触るか声をかける。`make seed` は全員のデータが消える点も共有する |

### 8.2 コミット前のチェック

Go をローカルに入れていなくても、Docker 経由で整形と静的解析ができる。

```bash
docker run --rm -v "$PWD/webapp/go":/src -w /src golang:1.22-alpine \
  sh -c "gofmt -l . && go vet ./... && go build ./..."
```

- `gofmt -l .` は**整形されていないファイル名を並べる**。何も出なければ OK。整形する場合は `gofmt -w .`。
- `go vet` は「文法は通るが怪しい書き方」を指摘する。
- `go build ./...` でコンパイルが通ることを確認する。

設計書を直した場合は `make docs` で xlsx も作り直してからコミットする。

---

## 9. 参考リンク

| 対象 | URL |
|------|-----|
| Go 公式ツアー (日本語あり) | <https://go.dev/tour/> |
| Effective Go | <https://go.dev/doc/effective_go> |
| Gin ドキュメント | <https://gin-gonic.com/docs/> |
| GORM ドキュメント (日本語) | <https://gorm.io/ja_JP/docs/> |
| GORM のクエリ一覧 | <https://gorm.io/ja_JP/docs/query.html> |
| Next.js Pages Router | <https://nextjs.org/docs/pages> |
