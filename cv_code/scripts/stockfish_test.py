import chess
import chess.engine
import time

stockfish_path = "../venv/Stockfish/src/stockfish"
engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

board = chess.Board()
board.set_fen("8/8/8/8/8/3k4/8/3K4 w - - 0 1")

print(board)
print()

while not board.is_game_over():
	result = engine.play(board, chess.engine.Limit(time=0.1))
	board.push(result.move)
	#result = engine.play(board, chess.engine.Limit(time=0.1))
	#board.push(result.move)
	#time.sleep(0.5)
	print("\033c")
	print(board)
print(board.result())

engine.quit()
