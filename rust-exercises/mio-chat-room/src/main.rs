extern crate mio;

use std::io::Cursor;
use std::env;
use std::str;
use std::net::SocketAddr;
use mio::util::Slab;
use mio::tcp::{TcpListener, TcpStream};
use mio::*;


struct MyHandler {
    server: TcpListener,
    conns: Slab<Connection>,
}

impl MyHandler {
    fn new(server: TcpListener) -> MyHandler {
        let conns = Slab::new_starting_at(Token(1), 1024);

        MyHandler {
            server: server,
            conns: conns,
        }
    }
}

impl Handler for MyHandler {
    type Timeout = ();
    type Message = ();

    fn ready(&mut self, event_loop: &mut EventLoop<MyHandler>, token: Token, events: EventSet) {
        match token {
            Token(0) => {
                if !events.is_readable() {
                    return;
                }

                match self.server.accept() {
                    Ok(Some(conn)) => {
                        println!("New connection.");
                        self.add_connection(event_loop, conn);
                    },
                    Ok(None) => println!("Hold, not ready yet."),
                    Err(e) => println!("Server accept error: {}", e),
                }
            }
            _ => {
                if self.conns[token].is_closed() {
                    self.dispatch(token);
                    self.conns.remove(token);
                    println!("Connection {:?} closed.", token);
                } else {
                    self.conns[token].handle(event_loop, events);
                    self.dispatch(token);
                }
            }
        }
    }
}

impl MyHandler {
    fn add_connection(&mut self, event_loop: &mut EventLoop<MyHandler>, conn: TcpStream) {
        let token = self.conns.insert_with(|token| Connection::new(conn, token)).unwrap();
        event_loop.register_opt(
            &self.conns[token].socket,
            token,
            EventSet::readable() | EventSet::hup(),
            PollOpt::level()
        ).unwrap();
    }

    fn dispatch(&mut self, token: Token) {
        if self.conns[token].buf.len() == 0 {
            return;
        }

        let mut buf = Cursor::new(self.conns[token].buf.clone());

        for conn in self.conns.iter_mut() {
            if conn.token != token && !conn.is_closed() {
                while buf.has_remaining() {
                    match conn.socket.try_write_buf(&mut buf) {
                        Ok(Some(0)) => {}
                        Ok(Some(_)) => {
                            if let Ok(s) = str::from_utf8(&buf.get_ref()) {
                                println!("{} => {}: {:?}",
                                    token.as_usize(),
                                    conn.token.as_usize(),
                                    s
                                );
                            } else {
                                println!("Invalid UTF-8 sequence");
                            }
                        }
                        Ok(None) => {
                            println!("Not actually ready");
                        }
                        Err(e) => {
                            println!("Something error when write: {}", e);
                            break;
                        }
                    }
                }

                buf.set_position(0);
            }
        }

        self.conns[token].buf.clear();
    }
}


struct Connection {
    socket: TcpStream,
    token: Token,
    closed: bool,
    buf: Vec<u8>,
}

impl Connection {
    fn new(socket: TcpStream, token: Token) -> Connection {
        Connection {
            socket: socket,
            token: token,
            closed: false,
            buf: Vec::new()
        }
    }

    fn handle(&mut self, event_loop: &mut EventLoop<MyHandler>, events: EventSet) {
        if events.is_hup() {
            self.close();
        } else if events.is_readable() {
            match self.socket.try_read_buf(&mut self.buf) {
                Ok(None) => {
                    self.close();
                    println!("Connection {:?} closing.", self.token);
                }
                Ok(Some(_)) => {
                    if let Ok(s) = str::from_utf8(&self.buf) {
                        println!("  <= {}: {:?}", self.token.as_usize(), s);
                    } else {
                        println!("Invalid UTF-8 sequence");
                    }
                }
                Err(e) => {
                    println!("Something error when read: {}", e);
                }
            }
        }
    }

    fn close(&mut self) {
        self.closed = true;
    }

    fn is_closed(&self) -> bool {
        return self.closed;
    }
}


fn start(address: SocketAddr) {
    let server = TcpListener::bind(&address).unwrap();

    let mut event_loop = EventLoop::new().unwrap();
    event_loop.register(&server, Token(0)).unwrap();

    let mut myhandler = MyHandler::new(server);
    event_loop.run(&mut myhandler).unwrap();
}

fn main() {
    let args: Vec<_> = env::args().collect();
    if args.len() < 2 {
        println!("Usage: cargo run <host:port>");
        return;
    }

    let addr_str = &args[1];
    let address = addr_str.parse().unwrap();

    start(address);
}
