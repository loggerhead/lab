extern crate mio;

use std::io::Cursor;
use std::env;
use std::str;
use std::net::SocketAddr;
use mio::util::Slab;
use mio::tcp::{TcpListener, TcpStream};
use mio::*;


const SERVER_TOKEN_NO: usize = 0;


struct MyHandler {
    server: TcpListener,
    conns: Slab<Connection>,
}

impl MyHandler {
    fn new(server: TcpListener) -> MyHandler {
        let conns = Slab::new_starting_at(Token(SERVER_TOKEN_NO + 1), 8192);

        MyHandler {
            server: server,
            conns: conns,
        }
    }

    fn add_connection(&mut self, event_loop: &mut EventLoop<MyHandler>, conn: TcpStream) {
        let token = self.conns.insert_with(|token| Connection::new(conn, token)).unwrap();
        event_loop.register(
            &self.conns[token].socket,
            token,
            EventSet::readable() | EventSet::hup() | EventSet::error(),
            PollOpt::level()
        ).unwrap();
    }
}

impl Handler for MyHandler {
    type Timeout = ();
    type Message = ();

    fn ready(&mut self, event_loop: &mut EventLoop<MyHandler>, token: Token, events: EventSet) {
        match token {
            Token(SERVER_TOKEN_NO) => {
                if !events.is_readable() {
                    return;
                }

                match self.server.accept() {
                    Ok(Some((conn, _addr))) => {
                        println!("New connection.");
                        self.add_connection(event_loop, conn);
                    },
                    Ok(None) => println!("Hold, not ready yet."),
                    Err(e) => println!("Server accept error: {}", e),
                }
            }
            _ => {
                self.conns[token].handle(event_loop, events);

                if self.conns[token].is_closed() {
                    self.conns.remove(token);
                    println!("Connection {:?} closed.", token);
                }
            }
        }
    }
}


struct Connection {
    socket: TcpStream,
    token: Token,
    closed: bool,
    buf: Cursor<Vec<u8>>,
    }

impl Connection {
    fn new(socket: TcpStream, token: Token) -> Connection {
        Connection {
            socket: socket,
            token: token,
            closed: false,
            buf: Cursor::new(Vec::new())
        }
    }

    fn handle(&mut self, event_loop: &mut EventLoop<MyHandler>, events: EventSet) {
        if events.is_error() {
            self.close();
            return;
        }

        if events.is_readable() || events.is_hup() {
            match self.socket.try_read_buf(self.buf.get_mut()) {
                Ok(None) | Ok(Some(0)) => {
                    self.close();
                }
                Ok(Some(_)) => {
                    println!("Get {:?}: {:?}", self.token, self.buf.get_ref());

                    event_loop.reregister(
                        &self.socket,
                        self.token,
                        EventSet::all(),
                        PollOpt::level()
                    ).unwrap();
                }
                Err(e) => {
                    println!("Something error when read: {}", e);
                }
            }
        }

        if events.is_writable() {
            match self.socket.try_write_buf(&mut self.buf) {
                Ok(_) => { }
                Err(e) => {
                    println!("Something error when write: {}", e);
                }
            }

            if self.no_more_data() {
                event_loop.reregister(
                    &self.socket,
                    self.token,
                    EventSet::readable() | EventSet::hup() | EventSet::error(),
                    PollOpt::level()
                ).unwrap();
            }
        }
    }

    fn close(&mut self) {
        self.closed = true;
    }

    fn is_closed(&self) -> bool {
        self.closed && self.no_more_data()
    }

    fn no_more_data(&self) -> bool {
        (self.buf.position() as usize) == self.buf.get_ref().len()
    }
}


fn start(address: SocketAddr) {
    let server = TcpListener::bind(&address).unwrap();

    let mut event_loop = EventLoop::new().unwrap();
    event_loop.register(
        &server,
        Token(SERVER_TOKEN_NO),
        EventSet::readable() | EventSet::hup() | EventSet::error(),
        PollOpt::level()
    ).unwrap();

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
